from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Project, Sprint, Task, User


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[[Session, User, dict[str, Any]], dict[str, Any]]


def _project_to_dict(project: Project) -> dict[str, Any]:
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
    }


def _task_to_dict(task: Task) -> dict[str, Any]:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "issue_type": task.issue_type,
        "story_points": task.story_points,
        "due_date": task.due_date,
        "project_id": task.project_id,
        "sprint_id": task.sprint_id,
    }


def _sprint_to_dict(sprint: Sprint, tasks: list[Task] | None = None) -> dict[str, Any]:
    sprint_tasks = tasks or []
    completed_tasks = [task for task in sprint_tasks if task.status == "done"]
    return {
        "id": sprint.id,
        "name": sprint.name,
        "goal": sprint.goal,
        "status": sprint.status,
        "start_date": sprint.start_date,
        "end_date": sprint.end_date,
        "project_id": sprint.project_id,
        "total_tasks": len(sprint_tasks),
        "completed_tasks": len(completed_tasks),
        "total_story_points": sum(task.story_points or 0 for task in sprint_tasks),
        "completed_story_points": sum(task.story_points or 0 for task in completed_tasks),
    }


def create_project(db: Session, user: User, args: dict[str, Any]) -> dict[str, Any]:
    project = Project(
        name=args["name"],
        description=args.get("description"),
        status=args.get("status", "active"),
        owner_id=user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return {"project": _project_to_dict(project)}


def list_projects(db: Session, user: User, args: dict[str, Any]) -> dict[str, Any]:
    projects = db.scalars(select(Project).where(Project.owner_id == user.id).order_by(Project.created_at.desc())).all()
    return {"projects": [_project_to_dict(project) for project in projects]}


def delete_project(db: Session, user: User, args: dict[str, Any]) -> dict[str, Any]:
    project_id = args.get("project_id")
    project_name = args.get("project_name")

    if project_id is not None:
        project = db.scalar(select(Project).where(Project.id == project_id, Project.owner_id == user.id))
    elif project_name:
        project = db.scalar(select(Project).where(Project.name == project_name, Project.owner_id == user.id))
    else:
        return {"error": "Please provide a project id or project name."}

    if project is None:
        return {"error": "Project not found"}

    deleted_project = _project_to_dict(project)
    db.delete(project)
    db.commit()
    return {"project": deleted_project}


def create_task(db: Session, user: User, args: dict[str, Any]) -> dict[str, Any]:
    project_id = args.get("project_id")
    if project_id:
        project = db.scalar(select(Project).where(Project.id == project_id, Project.owner_id == user.id))
        if project is None:
            return {"error": "Project not found"}
    sprint_id = args.get("sprint_id")
    if sprint_id:
        sprint = db.scalar(select(Sprint).where(Sprint.id == sprint_id, Sprint.owner_id == user.id))
        if sprint is None:
            return {"error": "Sprint not found"}

    task = Task(
        title=args["title"],
        description=args.get("description"),
        status=args.get("status", "todo"),
        priority=args.get("priority", "medium"),
        issue_type=args.get("issue_type", "task"),
        story_points=args.get("story_points", 0),
        due_date=args.get("due_date"),
        project_id=project_id,
        sprint_id=sprint_id,
        owner_id=user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"task": _task_to_dict(task)}


def list_tasks(db: Session, user: User, args: dict[str, Any]) -> dict[str, Any]:
    query = select(Task).where(Task.owner_id == user.id)
    if args.get("status"):
        query = query.where(Task.status == args["status"])
    if args.get("project_id"):
        query = query.where(Task.project_id == args["project_id"])
    tasks = db.scalars(query.order_by(Task.created_at.desc())).all()
    return {"tasks": [_task_to_dict(task) for task in tasks]}


def update_task(db: Session, user: User, args: dict[str, Any]) -> dict[str, Any]:
    task = db.scalar(select(Task).where(Task.id == args["task_id"], Task.owner_id == user.id))
    if task is None:
        return {"error": "Task not found"}

    for key in ["title", "description", "status", "priority", "issue_type", "story_points", "due_date", "project_id", "sprint_id"]:
        if key in args and args[key] is not None:
            setattr(task, key, args[key])
    db.commit()
    db.refresh(task)
    return {"task": _task_to_dict(task)}


def create_sprint(db: Session, user: User, args: dict[str, Any]) -> dict[str, Any]:
    project_id = args.get("project_id")
    if project_id:
        project = db.scalar(select(Project).where(Project.id == project_id, Project.owner_id == user.id))
        if project is None:
            return {"error": "Project not found"}

    sprint = Sprint(
        name=args["name"],
        goal=args.get("goal"),
        status=args.get("status", "planned"),
        start_date=args.get("start_date"),
        end_date=args.get("end_date"),
        project_id=project_id,
        owner_id=user.id,
    )
    db.add(sprint)
    db.commit()
    db.refresh(sprint)
    return {"sprint": _sprint_to_dict(sprint)}


def list_sprints(db: Session, user: User, args: dict[str, Any]) -> dict[str, Any]:
    query = select(Sprint).where(Sprint.owner_id == user.id)
    if args.get("project_id"):
        query = query.where(Sprint.project_id == args["project_id"])
    sprints = db.scalars(query.order_by(Sprint.created_at.desc())).all()
    sprint_payload = []
    for sprint in sprints:
        tasks = db.scalars(select(Task).where(Task.sprint_id == sprint.id, Task.owner_id == user.id)).all()
        sprint_payload.append(_sprint_to_dict(sprint, tasks))
    return {"sprints": sprint_payload}


def update_sprint(db: Session, user: User, args: dict[str, Any]) -> dict[str, Any]:
    sprint = db.scalar(select(Sprint).where(Sprint.id == args["sprint_id"], Sprint.owner_id == user.id))
    if sprint is None:
        return {"error": "Sprint not found"}

    for key in ["name", "goal", "status", "start_date", "end_date", "project_id"]:
        if key in args and args[key] is not None:
            setattr(sprint, key, args[key])
    db.commit()
    db.refresh(sprint)
    tasks = db.scalars(select(Task).where(Task.sprint_id == sprint.id, Task.owner_id == user.id)).all()
    return {"sprint": _sprint_to_dict(sprint, tasks)}


def assign_task_to_sprint(db: Session, user: User, args: dict[str, Any]) -> dict[str, Any]:
    task = db.scalar(select(Task).where(Task.id == args["task_id"], Task.owner_id == user.id))
    if task is None:
        return {"error": "Task not found"}

    sprint = db.scalar(select(Sprint).where(Sprint.id == args["sprint_id"], Sprint.owner_id == user.id))
    if sprint is None:
        return {"error": "Sprint not found"}

    task.sprint_id = sprint.id
    if sprint.project_id and task.project_id is None:
        task.project_id = sprint.project_id
    db.commit()
    db.refresh(task)
    return {"task": _task_to_dict(task), "sprint": _sprint_to_dict(sprint)}


TOOLS: dict[str, ToolDefinition] = {
    "create_project": ToolDefinition(
        name="create_project",
        description="Create a new project for the current user.",
        parameters={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "status": {"type": "string", "enum": ["active", "paused", "completed"]},
            },
            "required": ["name"],
        },
        handler=create_project,
    ),
    "list_projects": ToolDefinition(
        name="list_projects",
        description="List all projects for the current user.",
        parameters={"type": "object", "properties": {}},
        handler=list_projects,
    ),
    "delete_project": ToolDefinition(
        name="delete_project",
        description="Delete a project by id or exact project name for the current user. This also deletes tasks attached to that project.",
        parameters={
            "type": "object",
            "properties": {
                "project_id": {"type": "integer", "description": "The id of the project to delete"},
                "project_name": {"type": "string", "description": "The exact name of the project to delete"},
            },
        },
        handler=delete_project,
    ),
    "create_task": ToolDefinition(
        name="create_task",
        description="Create a new task, optionally attached to a project.",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "status": {"type": "string", "enum": ["todo", "in_progress", "done"]},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                "issue_type": {"type": "string", "enum": ["story", "task", "bug", "epic"]},
                "story_points": {"type": "integer"},
                "due_date": {"type": "string", "description": "YYYY-MM-DD if provided"},
                "project_id": {"type": "integer"},
                "sprint_id": {"type": "integer"},
            },
            "required": ["title"],
        },
        handler=create_task,
    ),
    "list_tasks": ToolDefinition(
        name="list_tasks",
        description="List tasks, optionally filtered by status or project_id.",
        parameters={
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["todo", "in_progress", "done"]},
                "project_id": {"type": "integer"},
            },
        },
        handler=list_tasks,
    ),
    "update_task": ToolDefinition(
        name="update_task",
        description="Update an existing task by id.",
        parameters={
            "type": "object",
            "properties": {
                "task_id": {"type": "integer"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "status": {"type": "string", "enum": ["todo", "in_progress", "done"]},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                "issue_type": {"type": "string", "enum": ["story", "task", "bug", "epic"]},
                "story_points": {"type": "integer"},
                "due_date": {"type": "string"},
                "project_id": {"type": "integer"},
                "sprint_id": {"type": "integer"},
            },
            "required": ["task_id"],
        },
        handler=update_task,
    ),
    "create_sprint": ToolDefinition(
        name="create_sprint",
        description="Create a Jira-like sprint with optional goal, dates, status, and project_id.",
        parameters={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "goal": {"type": "string"},
                "status": {"type": "string", "enum": ["planned", "active", "completed"]},
                "start_date": {"type": "string", "description": "YYYY-MM-DD if provided"},
                "end_date": {"type": "string", "description": "YYYY-MM-DD if provided"},
                "project_id": {"type": "integer"},
            },
            "required": ["name"],
        },
        handler=create_sprint,
    ),
    "list_sprints": ToolDefinition(
        name="list_sprints",
        description="List sprints with task counts and story point progress.",
        parameters={
            "type": "object",
            "properties": {
                "project_id": {"type": "integer"},
            },
        },
        handler=list_sprints,
    ),
    "update_sprint": ToolDefinition(
        name="update_sprint",
        description="Update a sprint status, goal, dates, name, or project.",
        parameters={
            "type": "object",
            "properties": {
                "sprint_id": {"type": "integer"},
                "name": {"type": "string"},
                "goal": {"type": "string"},
                "status": {"type": "string", "enum": ["planned", "active", "completed"]},
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "project_id": {"type": "integer"},
            },
            "required": ["sprint_id"],
        },
        handler=update_sprint,
    ),
    "assign_task_to_sprint": ToolDefinition(
        name="assign_task_to_sprint",
        description="Assign an existing task to an existing sprint.",
        parameters={
            "type": "object",
            "properties": {
                "task_id": {"type": "integer"},
                "sprint_id": {"type": "integer"},
            },
            "required": ["task_id", "sprint_id"],
        },
        handler=assign_task_to_sprint,
    ),
}


def openrouter_tools() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            },
        }
        for tool in TOOLS.values()
    ]
