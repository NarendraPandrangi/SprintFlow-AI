from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Project, Sprint, Task, User
from app.schemas import SprintCreate, SprintOut, SprintSummary, SprintUpdate


router = APIRouter(prefix="/sprints", tags=["sprints"])


def ensure_project_access(db: Session, project_id: int | None, user_id: int) -> None:
    if project_id is None:
        return
    project = db.scalar(select(Project).where(Project.id == project_id, Project.owner_id == user_id))
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")


def sprint_summary(db: Session, sprint: Sprint) -> SprintSummary:
    tasks = db.scalars(select(Task).where(Task.sprint_id == sprint.id, Task.owner_id == sprint.owner_id)).all()
    completed = [task for task in tasks if task.status == "done"]
    return SprintSummary(
        **SprintOut.model_validate(sprint).model_dump(),
        total_tasks=len(tasks),
        completed_tasks=len(completed),
        total_story_points=sum(task.story_points or 0 for task in tasks),
        completed_story_points=sum(task.story_points or 0 for task in completed),
    )


@router.get("", response_model=list[SprintSummary])
def list_sprints(
    project_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Sprint).where(Sprint.owner_id == user.id)
    if project_id:
        query = query.where(Sprint.project_id == project_id)
    sprints = db.scalars(query.order_by(Sprint.created_at.desc())).all()
    return [sprint_summary(db, sprint) for sprint in sprints]


@router.post("", response_model=SprintOut, status_code=status.HTTP_201_CREATED)
def create_sprint(
    payload: SprintCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ensure_project_access(db, payload.project_id, user.id)
    sprint = Sprint(**payload.model_dump(), owner_id=user.id)
    db.add(sprint)
    db.commit()
    db.refresh(sprint)
    return sprint


@router.patch("/{sprint_id}", response_model=SprintOut)
def update_sprint(
    sprint_id: int,
    payload: SprintUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sprint = db.scalar(select(Sprint).where(Sprint.id == sprint_id, Sprint.owner_id == user.id))
    if sprint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found")

    updates = payload.model_dump(exclude_unset=True)
    ensure_project_access(db, updates.get("project_id"), user.id)
    for key, value in updates.items():
        setattr(sprint, key, value)
    db.commit()
    db.refresh(sprint)
    return sprint


@router.delete("/{sprint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sprint(
    sprint_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sprint = db.scalar(select(Sprint).where(Sprint.id == sprint_id, Sprint.owner_id == user.id))
    if sprint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found")

    for task in db.scalars(select(Task).where(Task.sprint_id == sprint.id, Task.owner_id == user.id)):
        task.sprint_id = None
    db.delete(sprint)
    db.commit()
    return None
