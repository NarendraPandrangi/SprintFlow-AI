from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = None
    status: str = "active"


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = None
    status: str | None = None


class ProjectOut(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SprintBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    goal: str | None = None
    status: str = "planned"
    start_date: str | None = None
    end_date: str | None = None
    project_id: int | None = None


class SprintCreate(SprintBase):
    pass


class SprintUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    goal: str | None = None
    status: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    project_id: int | None = None


class SprintOut(SprintBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SprintSummary(SprintOut):
    total_tasks: int = 0
    completed_tasks: int = 0
    total_story_points: int = 0
    completed_story_points: int = 0


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    description: str | None = None
    status: str = "todo"
    priority: str = "medium"
    issue_type: str = "task"
    story_points: int = 0
    due_date: str | None = None
    project_id: int | None = None
    sprint_id: int | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=180)
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    issue_type: str | None = None
    story_points: int | None = None
    due_date: str | None = None
    project_id: int | None = None
    sprint_id: int | None = None


class TaskOut(TaskBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ToolCallOut(BaseModel):
    name: str
    arguments: dict
    result: dict


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[ToolCallOut] = []
