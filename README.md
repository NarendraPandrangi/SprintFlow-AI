# MCP-Based AI Assistant

A modern full-stack AI assistant for project and task management. Users chat with the assistant to create projects, add tasks, list work, and update progress. The backend exposes normal REST endpoints and an MCP-style tool registry that the AI layer can invoke through OpenRouter function calling.
<img width="1307" height="837" alt="Screenshot 2026-05-27 125425" src="https://github.com/user-attachments/assets/a2d4502a-d960-44b3-8d9b-8dbb586ef7a4" />

<img width="1329" height="839" alt="Screenshot 2026-05-27 130348" src="https://github.com/user-attachments/assets/c7b26bbd-669c-4cc4-b835-d5b66bd0ea88" />



## Tech Stack

| Technology | Purpose |
| --- | --- |
| React + Vite | Frontend development |
| Tailwind CSS | UI styling |
| FastAPI | Backend API development |
| Python | Backend programming |
| MySQL | Database management |
| SQLAlchemy | ORM for database operations |
| OpenRouter API | AI model integration |
| JWT Authentication | Secure user login |
| Axios | API communication |

## Project Structure

```text
backend/
  app/
    routers/          API routes for auth, projects, tasks, chat
    services/         AI agent and MCP-style tool registry
    config.py         Environment settings
    database.py       SQLAlchemy connection
    models.py         User, Project, Task models
    schemas.py        Pydantic request/response schemas
frontend/
  src/
    App.jsx           Main React application
    api.js            Axios API client
    styles.css        Tailwind entrypoint
```

## Database Setup

Create a MySQL database:

```sql
CREATE DATABASE mcp_assistant;
```

The FastAPI app creates the required tables automatically on startup.

## Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Update `backend/.env` with your MySQL credentials and, optionally, your OpenRouter API key:

```env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/mcp_assistant
JWT_SECRET_KEY=replace-with-a-strong-secret
OPENROUTER_API_KEY=your-openrouter-key
OPENROUTER_MODEL=openai/gpt-4o-mini
```

If `OPENROUTER_API_KEY` is empty, the chat still supports simple commands such as `create project Website`, `create task Design login page`, `list projects`, and `list tasks`.

## Frontend Setup

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Open `http://localhost:5173`.

## Core API

- `POST /auth/register`
- `POST /auth/login`
- `GET /projects`
- `POST /projects`
- `GET /tasks`
- `POST /tasks`
- `POST /chat`

## Example Chat Commands

- `create project Website Redesign`
- `create task Draft homepage copy`
- `list projects`
- `list tasks`
- `mark task 3 as done` with OpenRouter enabled

