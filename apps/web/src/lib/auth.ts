export interface StoredSession {
  user_id: number;
  name: string;
  onboarding_complete: boolean;
}

export function saveSession(session: StoredSession): void {
  localStorage.setItem("user_id", String(session.user_id));
  localStorage.setItem("user_name", session.name);
  localStorage.setItem("onboarding_complete", String(session.onboarding_complete));
}

export function clearSession(): void {
  localStorage.removeItem("user_id");
  localStorage.removeItem("user_name");
  localStorage.removeItem("onboarding_complete");
}

export function getSession(): StoredSession | null {
  if (typeof window === "undefined") return null;
  const user_id = localStorage.getItem("user_id");
  const name = localStorage.getItem("user_name");
  if (!user_id || !name) return null;
  return {
    user_id: Number(user_id),
    name,
    onboarding_complete: localStorage.getItem("onboarding_complete") === "true",
  };
}

export function isLoggedIn(): boolean {
  return getSession() !== null;
}
