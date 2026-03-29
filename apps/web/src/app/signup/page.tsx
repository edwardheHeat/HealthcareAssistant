"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { signup } from "@/lib/apiClient";
import { saveSession } from "@/lib/auth";

export default function SignupPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    name: "",
    account_id: "",
    password: "",
    confirm: "",
    age: "",
    sex: "" as "M" | "F" | "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = (field: string, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const handleSubmit = async () => {
    setError(null);
    if (!form.name || !form.account_id || !form.password || !form.age || !form.sex) {
      setError("All fields are required.");
      return;
    }
    if (form.password !== form.confirm) {
      setError("Passwords do not match.");
      return;
    }
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setLoading(true);
    try {
      const user = await signup({
        name: form.name,
        account_id: form.account_id,
        password: form.password,
        age: parseInt(form.age),
        sex: form.sex as "M" | "F",
      });
      saveSession({
        user_id: user.id,
        name: user.name,
        onboarding_complete: user.onboarding_complete,
      });
      router.push("/onboarding");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Signup failed.";
      setError(msg.includes("409") || msg.includes("taken") ? "That account ID is already taken." : msg);
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

        <h2 className="auth-title">Create your account</h2>
        <p className="auth-subtitle">Start tracking your health in minutes</p>

        {error && (
          <div className="alert-banner" style={{ marginBottom: 20 }}>
            ⚠️ {error}
          </div>
        )}

        <div className="form-section">
          <div className="form-group">
            <label className="form-label">Full name</label>
            <input
              className="form-input"
              type="text"
              placeholder="Jane Smith"
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Account ID</label>
            <input
              className="form-input"
              type="text"
              placeholder="janesmith — used to log in"
              value={form.account_id}
              onChange={(e) => set("account_id", e.target.value)}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Age</label>
              <input
                className="form-input"
                type="number"
                placeholder="e.g. 34"
                value={form.age}
                onChange={(e) => set("age", e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Biological sex</label>
              <select
                className="form-select"
                value={form.sex}
                onChange={(e) => set("sex", e.target.value)}
              >
                <option value="">Select…</option>
                <option value="M">Male</option>
                <option value="F">Female</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              className="form-input"
              type="password"
              placeholder="At least 8 characters"
              value={form.password}
              onChange={(e) => set("password", e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Confirm password</label>
            <input
              className="form-input"
              type="password"
              placeholder="Repeat your password"
              value={form.confirm}
              onChange={(e) => set("confirm", e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            />
          </div>

          <button
            className="btn btn-primary"
            style={{ width: "100%", marginTop: 4 }}
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading ? "Creating account…" : "Create account →"}
          </button>
        </div>

        <div className="auth-footer">
          Already have an account?{" "}
          <Link href="/login">Log in</Link>
        </div>
      </div>
    </div>
  );
}
