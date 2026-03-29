import { request, BASE_URL } from "./api";
import type { UserProfile, UserProfileCreate } from "@/types/user";
import type {
  BasicIndicatorRecord,
  DietRecord,
  SleepRecord,
  ExerciseRecord,
  PeriodRecord,
} from "@/types/health";
import type { HealthStats, Alert } from "@/types/stats";
import type { ChatSession, ChatMessage, ChatResponse } from "@/types/chat";

// ---- User ---------------------------------------------------------------- //
export const getMe = () => request<UserProfile>("/users/me");
export const createUser = (data: UserProfileCreate) =>
  request<UserProfile>("/users", { method: "POST", body: JSON.stringify(data) });

// ---- Health Records ------------------------------------------------------ //
export const postBasicIndicators = (data: { height_ft: number; weight_lbs: number }) =>
  request<BasicIndicatorRecord>("/health/basic-indicators", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const getBasicIndicators = (limit = 30) =>
  request<BasicIndicatorRecord[]>(`/health/basic-indicators?limit=${limit}`);

export const postDiet = (formData: FormData) =>
  fetch(`${BASE_URL}/health/diet`, { method: "POST", body: formData }).then(
    (r) => r.json() as Promise<DietRecord>,
  );

export const getDiet = (limit = 30) =>
  request<DietRecord[]>(`/health/diet?limit=${limit}`);

export const postSleep = (data: { sleep_start: string; wake_time: string }) =>
  request<SleepRecord>("/health/sleep", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const getSleep = (limit = 30) =>
  request<SleepRecord[]>(`/health/sleep?limit=${limit}`);

export const postExercise = (data: {
  work_activity_level: string;
  exercise_type: string;
  exercise_intensity: string;
  duration_min: number;
}) =>
  request<ExerciseRecord>("/health/exercise", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const getExercise = (limit = 30) =>
  request<ExerciseRecord[]>(`/health/exercise?limit=${limit}`);

export const postPeriod = (data: { has_flow: boolean; flow_amount?: string | null }) =>
  request<PeriodRecord>("/health/period", {
    method: "POST",
    body: JSON.stringify(data),
  });

// ---- Stats --------------------------------------------------------------- //
export const getStats = () => request<HealthStats>("/stats");

// ---- Alerts -------------------------------------------------------------- //
export const getAlerts = (unreadOnly = false) =>
  request<Alert[]>(`/alerts?unread_only=${unreadOnly}`);

export const markAlertRead = (id: number) =>
  request<Alert>(`/alerts/${id}/read`, { method: "PATCH" });

export const deleteAlert = (id: number) =>
  request<void>(`/alerts/${id}`, { method: "DELETE" });

export const deleteAlerts = (params: { afterDate?: string; beforeDate?: string }) => {
  const q = new URLSearchParams();
  if (params.afterDate) q.set("after_date", params.afterDate);
  if (params.beforeDate) q.set("before_date", params.beforeDate);
  const qs = q.toString() ? `?${q.toString()}` : "";
  return request<void>(`/alerts${qs}`, { method: "DELETE" });
};

// ---- Chat ---------------------------------------------------------------- //
export const createChatSession = () =>
  request<ChatSession>("/chat/sessions", { method: "POST", body: "{}" });

export const getChatSessions = () =>
  request<ChatSession[]>("/chat/sessions");

export const sendMessage = (sessionId: number, content: string) =>
  request<ChatResponse>(`/chat/sessions/${sessionId}/messages`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });

export const getMessages = (sessionId: number) =>
  request<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`);
