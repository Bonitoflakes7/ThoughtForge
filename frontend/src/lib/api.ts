import type { Comment, Conversation, ForkType, Message, Report, Thought, ThoughtDetail, User } from "../types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api/v1";
const TOKEN_KEY = "thoughtforge_access_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail ?? `Request failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function login(email: string, password: string) {
  const result = await request<{ access_token: string }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
  setToken(result.access_token);
  return getCurrentUser();
}

export async function register(payload: { username: string; email: string; password: string; display_name: string }) {
  await request<User>("/auth/register", { method: "POST", body: JSON.stringify(payload) });
  return login(payload.email, payload.password);
}

export const getCurrentUser = () => request<User>("/auth/me");
export const getThoughts = (sort: "top" | "recent") => request<Thought[]>(`/thoughts?sort=${sort}`);
export const getThought = (id: string) => request<ThoughtDetail>(`/thoughts/${id}`);
export const createThought = (title: string, body: string) => request<Thought>("/thoughts", { method: "POST", body: JSON.stringify({ title, body }) });
export const likeThought = (id: string) => request<void>(`/thoughts/${id}/like`, { method: "POST" });
export const addComment = (id: string, body: string) => request<Comment>(`/thoughts/${id}/comments`, { method: "POST", body: JSON.stringify({ body }) });
export const likeComment = (id: string) => request<void>(`/thoughts/comments/${id}/like`, { method: "POST" });
export const createFork = (id: string, payload: { title: string; body: string; fork_type: ForkType }) => request<Thought>(`/thoughts/${id}/fork`, { method: "POST", body: JSON.stringify(payload) });
export const reportThought = (id: string, reason: string, details?: string) => request<Report>(`/thoughts/${id}/report`, { method: "POST", body: JSON.stringify({ reason, details }) });
export const reportComment = (id: string, reason: string, details?: string) => request<Report>(`/thoughts/comments/${id}/report`, { method: "POST", body: JSON.stringify({ reason, details }) });
export const getReports = () => request<{ reports: Report[]; open_count: number }>("/moderation/reports?status=open");
export const resolveReport = (id: string, action: "dismiss" | "hide" | "restore" | "deactivate_user", note?: string) => request<Report>(`/moderation/reports/${id}`, { method: "PATCH", body: JSON.stringify({ action, note }) });
export const getAdminUsers = () => request<User[]>("/admin/users");
export const updateUserRole = (id: string, role: User["role"]) => request<User>(`/admin/users/${id}/role`, { method: "PATCH", body: JSON.stringify({ role }) });
export const updateUserStatus = (id: string, is_active: boolean) => request<User>(`/admin/users/${id}/status`, { method: "PATCH", body: JSON.stringify({ is_active }) });
export const getConversations = () => request<Conversation[]>("/chat/conversations");
export const createDirectConversation = (username: string) => request<Conversation>(`/chat/direct/${encodeURIComponent(username)}`, { method: "POST" });
export const createGroupConversation = (name: string, usernames: string[]) => request<Conversation>("/chat/groups", { method: "POST", body: JSON.stringify({ name, usernames }) });
export const getMessages = (id: string) => request<Message[]>(`/chat/conversations/${id}/messages`);
export const sendChatMessage = (id: string, body: string) => request<Message>(`/chat/conversations/${id}/messages`, { method: "POST", body: JSON.stringify({ body }) });
export const markConversationRead = (id: string) => request<void>(`/chat/conversations/${id}/read`, { method: "POST" });
export const websocketUrl = (id: string) => `${(import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api/v1").replace(/^http/, "ws").replace("/api/v1", "")}/ws/chat/${id}`;
