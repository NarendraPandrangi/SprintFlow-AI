from sqlalchemy import create_engine
from sqlalchemy import inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def sync_runtime_schema() -> None:
    inspector = inspect(engine)
    if not inspector.has_table("tasks"):
        return

    columns = {column["name"] for column in inspector.get_columns("tasks")}
    statements = []
    if "issue_type" not in columns:
        statements.append("ALTER TABLE tasks ADD COLUMN issue_type VARCHAR(40) NOT NULL DEFAULT 'task'")
    if "story_points" not in columns:
        statements.append("ALTER TABLE tasks ADD COLUMN story_points INTEGER NOT NULL DEFAULT 0")
    if "sprint_id" not in columns:
        statements.append("ALTER TABLE tasks ADD COLUMN sprint_id INTEGER NULL")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
