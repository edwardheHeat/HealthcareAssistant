"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { completeOnboarding } from "@/lib/apiClient";
import { getSession, saveSession } from "@/lib/auth";

const TOTAL_STEPS = 3;

const GOALS = [
  { id: "weight", icon: "⚖️", label: "Manage weight" },
  { id: "sleep", icon: "😴", label: "Improve sleep" },
  { id: "fitness", icon: "🏃", label: "Build fitness" },
  { id: "diet", icon: "🥗", label: "Eat better" },
  { id: "cycle", icon: "🌙", label: "Track cycle" },
  { id: "stress", icon: "🧘", label: "Reduce stress" },
];

export default function OnboardingPage() {
  const router = useRouter();
  const session = getSession();
  const [step, setStep] = useState(0);
  const [selectedGoals, setSelectedGoals] = useState<string[]>([]);
  const [injuries, setInjuries] = useState("");
  const [surgeries, setSurgeries] = useState("");
  const [constraints, setConstraints] = useState("");
  const [activityLevel, setActivityLevel] = useState("sedentary");
  const [wantsCycleTracking, setWantsCycleTracking] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleGoal = (id: string) =>
    setSelectedGoals((prev) =>
      prev.includes(id) ? prev.filter((g) => g !== id) : [...prev, id]
    );

  const handleFinish = async () => {
    setLoading(true);
    setError(null);
    try {
      // Build clinical constraints from inputs
      const parts: string[] = [];
      if (constraints) parts.push(constraints);
      if (activityLevel === "sedentary") parts.push("Sedentary occupation.");
      if (wantsCycleTracking) parts.push("Wants cycle tracking.");
      if (selectedGoals.length > 0)
        parts.push(`Health goals: ${selectedGoals.join(", ")}.`);

      await completeOnboarding({
        injuries: injuries || null,
        surgeries: surgeries || null,
        constraints: parts.join(" ") || null,
      });

      // Update local session
      if (session) {
        saveSession({ ...session, onboarding_complete: true });
      }
      router.push("/dashboard");
    } catch (e: unknown) {
      setError("Something went wrong saving your profile. Please try again.");
      setLoading(false);
    }
  };

  const next = () => setStep((s) => Math.min(s + 1, TOTAL_STEPS - 1));
  const back = () => setStep((s) => Math.max(s - 1, 0));

  return (
    <div className="onboarding-page">
      <div className="onboarding-card">
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <div style={{ fontSize: "2rem", marginBottom: 4 }}>🫀</div>
          <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.02em" }}>
            Health<span style={{ color: "var(--accent)" }}>AI</span>
          </div>
        </div>

        {/* Step dots */}
        <div className="stepper-dots">
          {Array.from({ length: TOTAL_STEPS }).map((_, i) => (
            <div
              key={i}
              className={`stepper-dot ${i === step ? "active" : i < step ? "done" : ""}`}
            />
          ))}
        </div>

        {error && (
          <div className="alert-banner" style={{ marginBottom: 20 }}>
            ⚠️ {error}
          </div>
        )}

        {/* ─── Step 0: Goals ─────────────────────────────────── */}
        {step === 0 && (
          <div>
            <h2 className="step-title">What are your health goals?</h2>
            <p className="step-subtitle">
              Select all that apply — this helps personalise your AI assistant.
            </p>
            <div className="goal-grid">
              {GOALS.map((g) => (
                <button
                  key={g.id}
                  className={`goal-btn ${selectedGoals.includes(g.id) ? "selected" : ""}`}
                  onClick={() => toggleGoal(g.id)}
                >
                  <span style={{ fontSize: 16 }}>{g.icon}</span>
                  {g.label}
                </button>
              ))}
            </div>

            <div className="form-group" style={{ marginTop: 8 }}>
              <label className="form-label">Typical work activity level</label>
              <select
                className="form-select"
                value={activityLevel}
                onChange={(e) => setActivityLevel(e.target.value)}
              >
                <option value="sedentary">Sedentary — desk job, minimal walking</option>
                <option value="light">Light — teacher, some walking</option>
                <option value="moderate">Moderate — nurse, retail, on feet often</option>
                <option value="heavy">Heavy — construction, physical labour</option>
              </select>
            </div>
          </div>
        )}

        {/* ─── Step 1: Clinical history ──────────────────────── */}
        {step === 1 && (
          <div>
            <h2 className="step-title">Any medical history to share?</h2>
            <p className="step-subtitle">
              This helps the AI give safer, more relevant advice. All fields are optional.
            </p>

            <div className="form-group">
              <label className="form-label">Injuries</label>
              <textarea
                className="form-input"
                rows={2}
                placeholder="e.g. right knee ligament tear (2022)"
                value={injuries}
                onChange={(e) => setInjuries(e.target.value)}
                style={{ resize: "vertical" }}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Surgeries</label>
              <textarea
                className="form-input"
                rows={2}
                placeholder="e.g. appendectomy (2019)"
                value={surgeries}
                onChange={(e) => setSurgeries(e.target.value)}
                style={{ resize: "vertical" }}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Movement restrictions or hard limits</label>
              <textarea
                className="form-input"
                rows={2}
                placeholder="e.g. avoid high-impact exercise due to knee; no overhead pressing"
                value={constraints}
                onChange={(e) => setConstraints(e.target.value)}
                style={{ resize: "vertical" }}
              />
            </div>
          </div>
        )}

        {/* ─── Step 2: Preferences ───────────────────────────── */}
        {step === 2 && (
          <div>
            <h2 className="step-title">A couple of final preferences</h2>
            <p className="step-subtitle">
              You can always update these later from your profile.
            </p>

            <div
              style={{
                background: "var(--bg-elevated)",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius-md)",
                padding: "16px 18px",
                marginBottom: 16,
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: "0.9rem", marginBottom: 2 }}>
                  🌙 Menstrual cycle tracking
                </div>
                <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  Log flow, get cycle phase insights
                </div>
              </div>
              <button
                onClick={() => setWantsCycleTracking((v) => !v)}
                style={{
                  width: 44,
                  height: 24,
                  borderRadius: 12,
                  border: "none",
                  background: wantsCycleTracking ? "var(--accent)" : "var(--border)",
                  cursor: "pointer",
                  position: "relative",
                  transition: "background 0.2s",
                  flexShrink: 0,
                }}
              >
                <span
                  style={{
                    position: "absolute",
                    top: 3,
                    left: wantsCycleTracking ? 22 : 3,
                    width: 18,
                    height: 18,
                    borderRadius: "50%",
                    background: "#fff",
                    transition: "left 0.2s",
                  }}
                />
              </button>
            </div>

            <div
              style={{
                background: "var(--accent-soft)",
                border: "1px solid var(--border-active)",
                borderRadius: "var(--radius-md)",
                padding: "14px 18px",
                fontSize: "0.85rem",
                color: "var(--text-secondary)",
                lineHeight: 1.6,
              }}
            >
              ✅ You&apos;re all set! After this, you&apos;ll land on your dashboard.
              Start by logging your body metrics to see your stats come alive.
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="onboarding-nav">
          {step > 0 ? (
            <button className="btn btn-ghost" onClick={back} disabled={loading}>
              ← Back
            </button>
          ) : (
            <div />
          )}

          {step < TOTAL_STEPS - 1 ? (
            <button className="btn btn-primary" onClick={next}>
              Continue →
            </button>
          ) : (
            <button
              className="btn btn-primary"
              onClick={handleFinish}
              disabled={loading}
            >
              {loading ? "Saving…" : "Go to dashboard →"}
            </button>
          )}
        </div>

        <div style={{ textAlign: "center", marginTop: 16, fontSize: "0.8rem", color: "var(--text-muted)" }}>
          Step {step + 1} of {TOTAL_STEPS}
        </div>
      </div>
    </div>
  );
}
