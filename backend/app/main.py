from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine, sync_runtime_schema
from app.routers import auth, chat, projects, sprints, tasks


Base.metadata.create_all(bind=engine)
sync_runtime_schema()

app = FastAPI(title="MCP-Based AI Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(sprints.router)
app.include_router(tasks.router)
app.include_router(chat.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
