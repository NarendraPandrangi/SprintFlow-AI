import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export async function login(email, password) {
  const { data } = await api.post("/auth/login", { email, password });
  return data;
}

export async function register(name, email, password) {
  const { data } = await api.post("/auth/register", { name, email, password });
  return data;
}

export async function getProjects() {
  const { data } = await api.get("/projects");
  return data;
}

export async function deleteProject(projectId) {
  await api.delete(`/projects/${projectId}`);
}

export async function getTasks() {
  const { data } = await api.get("/tasks");
  return data;
}

export async function getSprints() {
  const { data } = await api.get("/sprints");
  return data;
}

export async function sendChat(message) {
  const { data } = await api.post("/chat", { message });
  return data;
}
