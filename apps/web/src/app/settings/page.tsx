"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { clearSession, getSession } from "@/lib/auth";
import { getMe } from "@/lib/apiClient";
import type { UserSession } from "@/types/user";

export default function SettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [loggingOut, setLoggingOut] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const session = getSession();
    if (!session) {
      router.replace("/login");
      return;
    }

    getMe()
      .then((profile) => setUser(profile))
      .catch(() => setError("We couldn't load your account details right now."))
      .finally(() => setLoading(false));
  }, [router]);

  const handleLogout = () => {
    setLoggingOut(true);
    clearSession();
    router.replace("/login");
  };

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}>
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h1>User Settings</h1>
        <p>
          Review your account details and sign out when you want to test a fresh
          session.
        </p>
      </div>

      {error && (
        <div className="alert-banner" style={{ marginBottom: 20 }}>
          {error}
        </div>
      )}

      <div className="grid-2">
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>
            Account
          </div>
          <div className="settings-list">
            <div className="settings-row">
              <span className="settings-label">Name</span>
              <span className="settings-value">{user?.name ?? "Unknown"}</span>
            </div>
            <div className="settings-row">
              <span className="settings-label">Account ID</span>
              <span className="settings-value">
                {user?.account_id ?? "Unknown"}
              </span>
            </div>
            <div className="settings-row">
              <span className="settings-label">Age</span>
              <span className="settings-value">{user?.age ?? "Unknown"}</span>
            </div>
            <div className="settings-row">
              <span className="settings-label">Sex</span>
              <span className="settings-value">
                {user?.sex === "M"
                  ? "Male"
                  : user?.sex === "F"
                    ? "Female"
                    : "Unknown"}
              </span>
            </div>
            <div className="settings-row">
              <span className="settings-label">Onboarding</span>
              <span className="settings-value">
                {user?.onboarding_complete ? "Complete" : "Not complete"}
              </span>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>
            Session
          </div>
          <p style={{ marginBottom: 20 }}>
            Signing out clears your local browser session and sends you back to
            the login page.
          </p>
          <button
            className="btn btn-ghost btn-danger"
            onClick={handleLogout}
            disabled={loggingOut}
          >
            {loggingOut ? "Signing out..." : "Log out"}
          </button>
        </div>
      </div>
    </div>
  );
}
