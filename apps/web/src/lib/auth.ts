export interface StoredSession {
  user_id: number;
  name: string;
  onboarding_complete: boolean;
}

const USER_ID_COOKIE = "ha_user_id";
const ONBOARDING_COOKIE = "ha_onboarding_complete";
const COOKIE_MAX_AGE = 60 * 60 * 24 * 30;

function setCookie(name: string, value: string, maxAge: number): void {
  if (typeof document === "undefined") return;
  document.cookie = `${name}=${encodeURIComponent(value)}; Path=/; Max-Age=${maxAge}; SameSite=Lax`;
}

function clearCookie(name: string): void {
  if (typeof document === "undefined") return;
  document.cookie = `${name}=; Path=/; Max-Age=0; SameSite=Lax`;
}

export function saveSession(session: StoredSession): void {
  localStorage.setItem("user_id", String(session.user_id));
  localStorage.setItem("user_name", session.name);
  localStorage.setItem("onboarding_complete", String(session.onboarding_complete));
  setCookie(USER_ID_COOKIE, String(session.user_id), COOKIE_MAX_AGE);
  setCookie(
    ONBOARDING_COOKIE,
    String(session.onboarding_complete),
    COOKIE_MAX_AGE,
  );
}

export function clearSession(): void {
  localStorage.removeItem("user_id");
  localStorage.removeItem("user_name");
  localStorage.removeItem("onboarding_complete");
  clearCookie(USER_ID_COOKIE);
  clearCookie(ONBOARDING_COOKIE);
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
