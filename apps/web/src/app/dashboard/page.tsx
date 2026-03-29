"use client";

import { useEffect, useState } from "react";
import { getStats, getAlerts, markAlertRead } from "@/lib/apiClient";
import type { HealthStats, Alert } from "@/types/stats";

function TrendBadge({ trend }: { trend: string | null }) {
  if (!trend || trend === "unknown") return null;
  const configs = {
    gaining: { cls: "trend-up", icon: "↑", label: "Gaining" },
    losing: { cls: "trend-down", icon: "↓", label: "Losing" },
    stable: { cls: "trend-stable", icon: "→", label: "Stable" },
  };
  const cfg = configs[trend as keyof typeof configs] ?? configs.stable;
  return (
    <span className={`trend ${cfg.cls}`}>
      {cfg.icon} {cfg.label}
    </span>
  );
}

function StatCard({
  title,
  value,
  unit,
  sub,
  icon,
  accent,
}: {
  title: string;
  value: string | number | null;
  unit?: string;
  sub?: React.ReactNode;
  icon: string;
  accent?: "teal" | "amber" | "rose" | "green" | "accent";
}) {
  const accentColor = accent ?? "accent";
  return (
    <div className="card" style={{ position: "relative", overflow: "hidden" }}>
      <div
        style={{
          position: "absolute",
          top: 12,
          right: 14,
          fontSize: "1.6rem",
          opacity: 0.18,
        }}
      >
        {icon}
      </div>
      <div className="card-title">{title}</div>
      {value != null ? (
        <div className="card-value">
          {value}
          {unit && (
            <span style={{ fontSize: "1rem", color: "var(--text-muted)", marginLeft: 4 }}>
              {unit}
            </span>
          )}
        </div>
      ) : (
        <div className="card-value" style={{ fontSize: "1rem", color: "var(--text-muted)" }}>
          No data yet
        </div>
      )}
      {sub && <div className="card-sub">{sub}</div>}
    </div>
  );
}

function CyclePhase({ phase }: { phase: string | null }) {
  const phases: Record<string, { label: string; accent: string }> = {
    menstrual: { label: "🔴 Menstrual", accent: "var(--rose)" },
    follicular: { label: "🌱 Follicular", accent: "var(--teal)" },
    ovulatory: { label: "✨ Ovulatory", accent: "var(--accent)" },
    luteal: { label: "🌙 Luteal", accent: "var(--amber)" },
    unknown: { label: "— Unknown", accent: "var(--text-muted)" },
  };
  const cfg = phases[phase ?? "unknown"] ?? phases.unknown;
  return (
    <span style={{ color: cfg.accent, fontWeight: 600, fontSize: "0.9rem" }}>
      {cfg.label}
    </span>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState<HealthStats | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getStats(), getAlerts(true)])
      .then(([s, a]) => {
        setStats(s);
        setAlerts(a);
      })
      .catch((e) => setError(e.message ?? "Failed to load dashboard"))
      .finally(() => setLoading(false));
  }, []);

  const dismissAlert = async (id: number) => {
    await markAlertRead(id);
    setAlerts((prev) => prev.filter((a) => a.id !== id));
  };

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}>
        <div className="spinner" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="empty-state">
        <div className="empty-icon">⚠️</div>
        <p>{error}</p>
        <p style={{ fontSize: "0.8rem", marginTop: 8 }}>
          Make sure the backend is running at localhost:8000
        </p>
      </div>
    );
  }

  const d = stats?.diet;
  const sl = stats?.sleep;
  const ex = stats?.exercise;
  const per = stats?.period;

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Your health at a glance — updated from your latest logs</p>
      </div>

      {/* Active Alerts */}
      {alerts.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 28 }}>
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`alert-banner ${alert.alert_type === "stale" ? "alert-banner-stale" : ""}`}
            >
              <span>{alert.alert_type === "abnormal" ? "⚠️" : "⏰"}</span>
              <span style={{ flex: 1 }}>{alert.message}</span>
              <button
                onClick={() => dismissAlert(alert.id)}
                style={{
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  color: "inherit",
                  fontSize: "1rem",
                  padding: "0 4px",
                }}
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Body Metrics */}
      <h3 style={{ color: "var(--text-secondary)", marginBottom: 12, fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
        Body Metrics
      </h3>
      <div className="stat-grid" style={{ marginBottom: 28 }}>
        <StatCard
          title="BMI"
          value={stats?.bmi ?? null}
          icon="⚖️"
          accent="accent"
          sub={
            stats?.bmi ? (
              <span>
                {stats.bmi < 18.5
                  ? "Underweight"
                  : stats.bmi < 25
                  ? "Normal range"
                  : stats.bmi < 30
                  ? "Overweight"
                  : "Obese range"}
              </span>
            ) : null
          }
        />
        <StatCard
          title="Weight"
          value={stats?.current_weight_lbs ?? null}
          unit="lbs"
          icon="🏋️"
          accent="teal"
          sub={<TrendBadge trend={stats?.weight_trend ?? null} />}
        />
        <StatCard
          title="Height"
          value={stats?.current_height_ft ?? null}
          unit="ft"
          icon="📏"
          accent="accent"
          sub={<TrendBadge trend={stats?.height_trend ?? null} />}
        />
      </div>

      {/* Diet */}
      <h3 style={{ color: "var(--text-secondary)", marginBottom: 12, fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
        Diet — 7-Day Average
      </h3>
      <div className="stat-grid" style={{ marginBottom: 28 }}>
        <StatCard
          title="Avg Daily Calories"
          value={d?.avg_calories_7d ?? null}
          unit="kcal"
          icon="🍽️"
          accent="amber"
          sub={
            d?.calorie_deficit_surplus_vs_tdee != null ? (
              <span
                style={{
                  color:
                    d.calorie_deficit_surplus_vs_tdee > 0
                      ? "var(--rose)"
                      : "var(--teal)",
                }}
              >
                {d.calorie_deficit_surplus_vs_tdee > 0 ? "+" : ""}
                {d.calorie_deficit_surplus_vs_tdee} kcal vs TDEE (
                {d.estimated_tdee} kcal)
              </span>
            ) : null
          }
        />
        <StatCard
          title="Protein"
          value={d?.avg_protein_g_7d ?? null}
          unit="g"
          icon="🥩"
          accent="green"
        />
        <StatCard
          title="Carbs"
          value={d?.avg_carbs_g_7d ?? null}
          unit="g"
          icon="🌾"
          accent="amber"
        />
        <StatCard
          title="Fat"
          value={d?.avg_fat_g_7d ?? null}
          unit="g"
          icon="🧈"
          accent="teal"
        />
      </div>

      {/* Sleep */}
      <h3 style={{ color: "var(--text-secondary)", marginBottom: 12, fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
        Sleep — 7-Day Average
      </h3>
      <div className="stat-grid" style={{ marginBottom: 28 }}>
        <StatCard
          title="Avg Sleep Duration"
          value={sl?.avg_duration_hrs_7d ?? null}
          unit="hrs"
          icon="😴"
          accent="accent"
          sub={
            sl?.deviation_from_recommended_hrs != null ? (
              <span>
                {sl.deviation_from_recommended_hrs === 0
                  ? "Within recommended range"
                  : `${sl.deviation_from_recommended_hrs} hrs from recommended 7–9 hrs`}
              </span>
            ) : null
          }
        />
        <StatCard
          title="Sleep Consistency"
          value={
            sl?.sleep_consistency_score != null ? `${sl.sleep_consistency_score}/100` : null
          }
          icon="🕐"
          accent="teal"
          sub={
            sl?.sleep_consistency_score != null ? (
              <span>
                {sl.sleep_consistency_score >= 80
                  ? "Very consistent"
                  : sl.sleep_consistency_score >= 60
                  ? "Moderately consistent"
                  : "Irregular schedule"}
              </span>
            ) : null
          }
        />
      </div>

      {/* Exercise */}
      <h3 style={{ color: "var(--text-secondary)", marginBottom: 12, fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
        Exercise — 30-Day
      </h3>
      <div className="stat-grid" style={{ marginBottom: 28 }}>
        <StatCard
          title="Avg Daily MET"
          value={ex?.avg_daily_met_30d ?? null}
          icon="🏃"
          accent="green"
          sub={<TrendBadge trend={ex?.activity_trend ?? null} />}
        />
        <StatCard
          title="Cardio Sessions / Week"
          value={ex?.cardio_sessions_per_week ?? null}
          icon="❤️"
          accent="rose"
        />
      </div>

      {/* Period */}
      {per && (
        <>
          <h3 style={{ color: "var(--text-secondary)", marginBottom: 12, fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Cycle
          </h3>
          <div className="stat-grid" style={{ marginBottom: 28 }}>
            <StatCard
              title="Current Phase"
              value={null}
              icon="🌙"
              accent="accent"
              sub={<CyclePhase phase={per.cycle_phase} />}
            />
            {per.current_flow_amount && (
              <StatCard
                title="Flow Amount"
                value={per.current_flow_amount}
                icon="💧"
                accent="rose"
              />
            )}
          </div>
        </>
      )}

      {/* Empty state */}
      {!stats?.current_weight_lbs &&
        !d?.avg_calories_7d &&
        !sl?.avg_duration_hrs_7d && (
          <div className="card" style={{ textAlign: "center", marginTop: 40 }}>
            <div style={{ fontSize: "3rem", marginBottom: 16 }}>📋</div>
            <h3>No health data yet</h3>
            <p style={{ marginTop: 8, marginBottom: 20 }}>
              Start logging your health metrics to see your dashboard come alive.
            </p>
            <a href="/questionnaire" className="btn btn-primary">
              Log My First Entry
            </a>
          </div>
        )}
    </div>
  );
}
