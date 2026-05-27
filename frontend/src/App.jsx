import { Bot, CheckCircle2, Flag, FolderKanban, LogOut, Send, Sparkles, Trash2, UserPlus } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { deleteProject, getProjects, getSprints, getTasks, login, register, sendChat } from "./api";

function AuthScreen({ onAuth }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data =
        mode === "login"
          ? await login(form.email, form.password)
          : await register(form.name, form.email, form.password);
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));
      onAuth(data.user);
    } catch (err) {
      setError(err.response?.data?.detail || "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-mist px-4">
      <section className="w-full max-w-md rounded-lg border border-line bg-white p-6 shadow-sm">
        <div className="mb-6 flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-md bg-ocean text-white">
            <Bot size={24} />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-ink">MCP Assistant</h1>
            <p className="text-sm text-slate-500">AI-powered project and task management</p>
          </div>
        </div>

        <div className="mb-5 grid grid-cols-2 rounded-md border border-line p-1">
          <button
            className={`rounded px-3 py-2 text-sm ${mode === "login" ? "bg-ink text-white" : "text-slate-600"}`}
            onClick={() => setMode("login")}
            type="button"
          >
            Login
          </button>
          <button
            className={`rounded px-3 py-2 text-sm ${mode === "register" ? "bg-ink text-white" : "text-slate-600"}`}
            onClick={() => setMode("register")}
            type="button"
          >
            Register
          </button>
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          {mode === "register" && (
            <label className="block">
              <span className="mb-1 block text-sm font-medium">Name</span>
              <input
                className="w-full rounded-md border border-line px-3 py-2 outline-none focus:border-ocean"
                onChange={(event) => setForm({ ...form, name: event.target.value })}
                required
                value={form.name}
              />
            </label>
          )}
          <label className="block">
            <span className="mb-1 block text-sm font-medium">Email</span>
            <input
              className="w-full rounded-md border border-line px-3 py-2 outline-none focus:border-ocean"
              onChange={(event) => setForm({ ...form, email: event.target.value })}
              required
              type="email"
              value={form.email}
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-sm font-medium">Password</span>
            <input
              className="w-full rounded-md border border-line px-3 py-2 outline-none focus:border-ocean"
              minLength={6}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
              required
              type="password"
              value={form.password}
            />
          </label>
          {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <button
            className="flex w-full items-center justify-center gap-2 rounded-md bg-coral px-4 py-2.5 font-semibold text-white disabled:opacity-60"
            disabled={loading}
            type="submit"
          >
            {mode === "register" ? <UserPlus size={18} /> : <Sparkles size={18} />}
            {loading ? "Please wait" : mode === "login" ? "Login" : "Create account"}
          </button>
        </form>
      </section>
    </main>
  );
}

function Metric({ icon: Icon, label, value }) {
  return (
    <div className="rounded-lg border border-line bg-white p-4">
      <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-md bg-mist text-ocean">
        <Icon size={19} />
      </div>
      <p className="text-2xl font-semibold">{value}</p>
      <p className="text-sm text-slate-500">{label}</p>
    </div>
  );
}

function ChatPanel({ onDataChanged }) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Tell me what to do. Try: create sprint Sprint 1, create task Draft homepage copy, assign task 2 to sprint 1, or list sprints.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function submitMessage(event) {
    event.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setMessages((current) => [...current, { role: "user", text }]);
    setInput("");
    setLoading(true);
    try {
      const data = await sendChat(text);
      setMessages((current) => [...current, { role: "assistant", text: data.reply }]);
      if (data.tool_calls?.length) {
        onDataChanged();
      }
    } catch (err) {
      setMessages((current) => [
        ...current,
        { role: "assistant", text: err.response?.data?.detail || "I could not process that request." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="flex min-h-[620px] flex-col rounded-lg border border-line bg-white">
      <div className="border-b border-line p-4">
        <div className="flex items-center gap-2 font-semibold">
          <Bot size={19} />
          Assistant chat
        </div>
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.map((message, index) => (
          <div
            className={`max-w-[86%] rounded-lg px-3 py-2 text-sm ${
              message.role === "user" ? "ml-auto bg-ocean text-white" : "bg-mist text-ink"
            }`}
            key={`${message.role}-${index}`}
          >
            {message.text}
          </div>
        ))}
        {loading && <div className="max-w-[86%] rounded-lg bg-mist px-3 py-2 text-sm text-slate-500">Thinking...</div>}
      </div>
      <form className="flex gap-2 border-t border-line p-3" onSubmit={submitMessage}>
        <input
          className="min-w-0 flex-1 rounded-md border border-line px-3 py-2 outline-none focus:border-ocean"
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask the assistant..."
          value={input}
        />
        <button className="grid h-10 w-10 place-items-center rounded-md bg-coral text-white" title="Send" type="submit">
          <Send size={18} />
        </button>
      </form>
    </section>
  );
}

function Dashboard({ user, onLogout }) {
  const [projects, setProjects] = useState([]);
  const [sprints, setSprints] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deletingProjectId, setDeletingProjectId] = useState(null);

  async function refreshData() {
    const [projectData, sprintData, taskData] = await Promise.all([getProjects(), getSprints(), getTasks()]);
    setProjects(projectData);
    setSprints(sprintData);
    setTasks(taskData);
  }

  useEffect(() => {
    refreshData().finally(() => setLoading(false));
  }, []);

  const completedTasks = useMemo(() => tasks.filter((task) => task.status === "done").length, [tasks]);
  const activeSprint = useMemo(() => sprints.find((sprint) => sprint.status === "active"), [sprints]);
  const totalStoryPoints = useMemo(() => tasks.reduce((sum, task) => sum + (task.story_points || 0), 0), [tasks]);

  async function handleDeleteProject(project) {
    const confirmed = window.confirm(`Delete "${project.name}" and its tasks?`);
    if (!confirmed) return;

    setDeletingProjectId(project.id);
    try {
      await deleteProject(project.id);
      await refreshData();
    } finally {
      setDeletingProjectId(null);
    }
  }

  return (
    <main className="min-h-screen bg-mist">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <div>
            <h1 className="text-xl font-semibold">MCP-Based AI Assistant</h1>
            <p className="text-sm text-slate-500">Welcome, {user.name}</p>
          </div>
          <button className="flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm" onClick={onLogout}>
            <LogOut size={16} />
            Logout
          </button>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-5 px-4 py-5 lg:grid-cols-[1fr_420px]">
        <section className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-4">
            <Metric icon={FolderKanban} label="Projects" value={projects.length} />
            <Metric icon={Flag} label="Sprints" value={sprints.length} />
            <Metric icon={CheckCircle2} label="Tasks" value={tasks.length} />
            <Metric icon={Sparkles} label="Story Points" value={totalStoryPoints} />
          </div>

          <section className="rounded-lg border border-line bg-white">
            <div className="flex items-center justify-between border-b border-line p-4">
              <div>
                <h2 className="font-semibold">Sprint Board</h2>
                <p className="text-sm text-slate-500">
                  {activeSprint ? `Active: ${activeSprint.name}` : "No active sprint"}
                </p>
              </div>
              <span className="rounded bg-mist px-2 py-1 text-xs text-slate-600">{completedTasks} done</span>
            </div>
            <div className="grid gap-3 p-4 md:grid-cols-3">
              {["todo", "in_progress", "done"].map((status) => (
                <div className="min-h-40 rounded-md border border-line bg-mist" key={status}>
                  <div className="border-b border-line px-3 py-2 text-sm font-semibold uppercase text-slate-600">
                    {status.replace("_", " ")}
                  </div>
                  <div className="space-y-2 p-2">
                    {tasks
                      .filter((task) => task.status === status)
                      .slice(0, 5)
                      .map((task) => (
                        <div className="rounded-md border border-line bg-white p-3 text-sm" key={task.id}>
                          <div className="mb-2 flex items-center justify-between gap-2">
                            <span className="font-medium">{task.title}</span>
                            <span className="rounded bg-mist px-2 py-0.5 text-xs">{task.story_points || 0} pts</span>
                          </div>
                          <div className="flex flex-wrap gap-2 text-xs text-slate-500">
                            <span>{task.issue_type}</span>
                            <span>{task.priority}</span>
                            {task.sprint_id && <span>Sprint #{task.sprint_id}</span>}
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              ))}
            </div>
          </section>

          <div className="grid gap-5 xl:grid-cols-2">
            <section className="rounded-lg border border-line bg-white">
              <div className="border-b border-line p-4 font-semibold">Projects</div>
              <div className="divide-y divide-line">
                {loading && <p className="p-4 text-sm text-slate-500">Loading projects...</p>}
                {!loading && projects.length === 0 && <p className="p-4 text-sm text-slate-500">No projects yet.</p>}
                {projects.map((project) => (
                  <article className="p-4" key={project.id}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h2 className="font-medium">{project.name}</h2>
                        <p className="mt-1 text-sm text-slate-500">{project.description || "No description"}</p>
                        <p className="mt-2 text-xs text-slate-500">ID: {project.id}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="rounded bg-mist px-2 py-1 text-xs text-slate-600">{project.status}</span>
                        <button
                          className="grid h-8 w-8 place-items-center rounded-md border border-line text-slate-500 hover:border-red-200 hover:bg-red-50 hover:text-red-700 disabled:opacity-50"
                          disabled={deletingProjectId === project.id}
                          onClick={() => handleDeleteProject(project)}
                          title="Delete project"
                          type="button"
                        >
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </section>

            <section className="rounded-lg border border-line bg-white">
              <div className="border-b border-line p-4 font-semibold">Sprints</div>
              <div className="divide-y divide-line">
                {loading && <p className="p-4 text-sm text-slate-500">Loading sprints...</p>}
                {!loading && sprints.length === 0 && <p className="p-4 text-sm text-slate-500">No sprints yet.</p>}
                {sprints.map((sprint) => (
                  <article className="p-4" key={sprint.id}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h2 className="font-medium">{sprint.name}</h2>
                        <p className="mt-1 text-sm text-slate-500">{sprint.goal || "No sprint goal"}</p>
                        <p className="mt-2 text-xs text-slate-500">
                          ID: {sprint.id} | {sprint.completed_story_points}/{sprint.total_story_points} points |{" "}
                          {sprint.completed_tasks}/{sprint.total_tasks} tasks
                        </p>
                      </div>
                      <span className="rounded bg-mist px-2 py-1 text-xs text-slate-600">{sprint.status}</span>
                    </div>
                  </article>
                ))}
              </div>
            </section>

            <section className="rounded-lg border border-line bg-white">
              <div className="border-b border-line p-4 font-semibold">Tasks</div>
              <div className="divide-y divide-line">
                {loading && <p className="p-4 text-sm text-slate-500">Loading tasks...</p>}
                {!loading && tasks.length === 0 && <p className="p-4 text-sm text-slate-500">No tasks yet.</p>}
                {tasks.map((task) => (
                  <article className="p-4" key={task.id}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h2 className="font-medium">{task.title}</h2>
                        <p className="mt-1 text-sm text-slate-500">{task.description || "No description"}</p>
                        <p className="mt-2 text-xs text-slate-500">
                          #{task.id} | {task.issue_type} | {task.story_points || 0} points
                          {task.sprint_id ? ` | Sprint #${task.sprint_id}` : ""}
                        </p>
                      </div>
                      <span className="rounded bg-mist px-2 py-1 text-xs text-slate-600">{task.priority}</span>
                    </div>
                    <p className="mt-2 text-xs uppercase text-slate-500">{task.status.replace("_", " ")}</p>
                  </article>
                ))}
              </div>
            </section>
          </div>
        </section>

        <ChatPanel onDataChanged={refreshData} />
      </div>
    </main>
  );
}

export default function App() {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem("user");
    return stored ? JSON.parse(stored) : null;
  });

  function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
  }

  if (!user) {
    return <AuthScreen onAuth={setUser} />;
  }

  return <Dashboard onLogout={logout} user={user} />;
}
