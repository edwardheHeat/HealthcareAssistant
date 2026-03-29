"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { login } from "@/lib/apiClient";
import { saveSession } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [accountId, setAccountId] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async () => {
    setError(null);
    if (!accountId || !password) {
      setError("Please fill in both fields.");
      return;
    }
    setLoading(true);
    try {
      const res = await login({ account_id: accountId, password });
      saveSession({
        user_id: res.user_id,
        name: res.name,
        onboarding_complete: res.onboarding_complete,
      });
      router.push(res.onboarding_complete ? "/dashboard" : "/onboarding");
    } catch (e: unknown) {
      setError("Invalid account ID or password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">
          <div className="auth-logo-icon">🫀</div>
          <div className="auth-logo-text">Health<span>AI</span></div>
        </div>

        <h2 className="auth-title">Welcome back</h2>
        <p className="auth-subtitle">Log in to view your health dashboard</p>

        {error && (
          <div className="alert-banner" style={{ marginBottom: 20 }}>
            ⚠️ {error}
          </div>
        )}

        <div className="form-section">
          <div className="form-group">
            <label className="form-label">Account ID</label>
            <input
              className="form-input"
              type="text"
              placeholder="Your account ID"
              value={accountId}
              onChange={(e) => setAccountId(e.target.value)}
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              className="form-input"
              type="password"
              placeholder="Your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleLogin()}
            />
          </div>

          <button
            className="btn btn-primary"
            style={{ width: "100%", marginTop: 4 }}
            onClick={handleLogin}
            disabled={loading}
          >
            {loading ? "Logging in…" : "Log in →"}
          </button>
        </div>

        <div className="auth-footer">
          Don&apos;t have an account?{" "}
          <Link href="/signup">Sign up</Link>
        </div>
      </div>
    </div>
  );
}
