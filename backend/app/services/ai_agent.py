import json
import re
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User
from app.services.mcp_tools import TOOLS, openrouter_tools


SYSTEM_PROMPT = """
You are an AI project assistant with Jira-like sprint planning tools. Help users
create projects, create sprints, manage tasks/issues, assign tasks to sprints,
retrieve work, delete projects, and summarize progress. Use tools whenever the
user asks to create, update, delete, assign, or retrieve project/task/sprint data.
Keep responses concise and useful.
"""


def _fallback_intent(message: str) -> tuple[str | None, dict[str, Any]]:
    text = message.strip()
    lowered = text.lower()

    if "list" in lowered and "project" in lowered:
        return "list_projects", {}
    if "list" in lowered and "sprint" in lowered:
        return "list_sprints", {}
    if "list" in lowered and "task" in lowered:
        return "list_tasks", {}

    project_match = re.match(r"^(create|add)\s+(a\s+)?project\s+(.+)$", text, flags=re.IGNORECASE)
    if project_match:
        name = project_match.group(3).strip(" :-")
        return "create_project", {"name": name or "Untitled project"}

    delete_project_match = re.search(r"(delete|remove)\s+project\s+#?(\d+)", lowered)
    if delete_project_match:
        return "delete_project", {"project_id": int(delete_project_match.group(2))}

    delete_project_name_match = re.match(r"^(delete|remove)\s+(the\s+)?project\s+(.+)$", text, flags=re.IGNORECASE)
    if delete_project_name_match:
        project_name = delete_project_name_match.group(3).strip(" :-")
        return "delete_project", {"project_name": project_name}

    task_match = re.match(r"^(create|add)\s+(a\s+)?task\s+(.+)$", text, flags=re.IGNORECASE)
    if task_match:
        title = task_match.group(3).strip(" :-")
        return "create_task", {"title": title or "Untitled task"}

    sprint_match = re.match(r"^(create|add)\s+(a\s+)?sprint\s+(.+)$", text, flags=re.IGNORECASE)
    if sprint_match:
        name = sprint_match.group(3).strip(" :-")
        return "create_sprint", {"name": name or "Untitled sprint"}

    assign_sprint_match = re.search(r"(assign|add|move)\s+task\s+#?(\d+)\s+(to|into)\s+sprint\s+#?(\d+)", lowered)
    if assign_sprint_match:
        return "assign_task_to_sprint", {
            "task_id": int(assign_sprint_match.group(2)),
            "sprint_id": int(assign_sprint_match.group(4)),
        }

    sprint_status_match = re.search(r"(start|activate|complete|finish)\s+sprint\s+#?(\d+)", lowered)
    if sprint_status_match:
        action = sprint_status_match.group(1)
        status = "completed" if action in {"complete", "finish"} else "active"
        return "update_sprint", {"sprint_id": int(sprint_status_match.group(2)), "status": status}

    done_match = re.search(r"(mark|set)\s+task\s+#?(\d+)\s+(as\s+)?(done|complete|completed)", lowered)
    if done_match:
        return "update_task", {"task_id": int(done_match.group(2)), "status": "done"}

    return None, {}


def _format_tool_result(tool_name: str, result: dict[str, Any]) -> str:
    if "error" in result:
        return result["error"]
    if tool_name == "create_project":
        return f"Created project: {result['project']['name']}."
    if tool_name == "delete_project":
        return f"Deleted project: {result['project']['name']}."
    if tool_name == "create_sprint":
        return f"Created sprint: {result['sprint']['name']}."
    if tool_name == "list_sprints":
        sprints = result["sprints"]
        if not sprints:
            return "You do not have any sprints yet."
        return "Sprints: " + ", ".join(
            f"{sprint['name']} ({sprint['status']}, {sprint['completed_story_points']}/{sprint['total_story_points']} pts)"
            for sprint in sprints
        )
    if tool_name == "update_sprint":
        return f"Updated sprint: {result['sprint']['name']}."
    if tool_name == "assign_task_to_sprint":
        return f"Assigned task '{result['task']['title']}' to sprint '{result['sprint']['name']}'."
    if tool_name == "create_task":
        return f"Created task: {result['task']['title']}."
    if tool_name == "list_projects":
        projects = result["projects"]
        if not projects:
            return "You do not have any projects yet."
        return "Projects: " + ", ".join(project["name"] for project in projects)
    if tool_name == "list_tasks":
        tasks = result["tasks"]
        if not tasks:
            return "You do not have any tasks yet."
        return "Tasks: " + ", ".join(f"{task['title']} ({task['status']})" for task in tasks)
    if tool_name == "update_task":
        return f"Updated task: {result['task']['title']}."
    return "Done."


async def run_assistant(message: str, db: Session, user: User) -> dict[str, Any]:
    if not settings.openrouter_api_key:
        tool_name, args = _fallback_intent(message)
        if tool_name is None:
            return {
                "reply": "I can help you create projects, create tasks, list projects, and list tasks. Add an OpenRouter API key for richer natural-language handling.",
                "tool_calls": [],
            }
        result = TOOLS[tool_name].handler(db, user, args)
        return {
            "reply": _format_tool_result(tool_name, result),
            "tool_calls": [{"name": tool_name, "arguments": args, "result": result}],
        }

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "MCP-Based AI Assistant",
    }
    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        "tools": openrouter_tools(),
        "tool_choice": "auto",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    assistant_message = data["choices"][0]["message"]
    tool_calls = []
    reply_parts = []

    for call in assistant_message.get("tool_calls", []) or []:
        function = call["function"]
        tool_name = function["name"]
        args = json.loads(function.get("arguments") or "{}")
        tool = TOOLS.get(tool_name)
        if tool is None:
            continue
        result = tool.handler(db, user, args)
        tool_calls.append({"name": tool_name, "arguments": args, "result": result})
        reply_parts.append(_format_tool_result(tool_name, result))

    if not reply_parts:
        reply_parts.append(assistant_message.get("content") or "I handled that.")

    return {"reply": " ".join(reply_parts), "tool_calls": tool_calls}
