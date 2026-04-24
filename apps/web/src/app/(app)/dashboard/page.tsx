"use client";

import { useEffect, useState } from "react";

import { getAlerts, getStats, markAlertRead } from "@/lib/apiClient";
import type {
  Alert,
  ChartPoint,
  DashboardResponse,
  IndicatorAnalysisPeriods,
} from "@/types/stats";

function StatCard({
  title,
  value,
  unit,
  sub,
  icon,
}: {
  title: string;
  value: string | number | null;
  unit?: string;
  sub?: React.ReactNode;
  icon: string;
}) {
  return (
    <div className="card" style={{ position: "relative", overflow: "hidden" }}>
      <div
        style={{
          position: "absolute",
          top: 12,
          right: 14,
          fontSize: "1rem",
          opacity: 0.2,
          fontWeight: 700,
        }}
      >
        {icon}
      </div>
      <div className="card-title">{title}</div>
      {value != null ? (
        <div className="card-value">
          {value}
          {unit && (
            <span
              style={{
                fontSize: "1rem",
                color: "var(--text-muted)",
                marginLeft: 4,
              }}
            >
              {unit}
            </span>
          )}
        </div>
      ) : (
        <div
          className="card-value"
          style={{ fontSize: "1rem", color: "var(--text-muted)" }}
        >
          No data yet
        </div>
      )}
      {sub && <div className="card-sub">{sub}</div>}
    </div>
  );
}

function DeltaBadge({
  value,
  unit = "",
}: {
  value: number | null;
  unit?: string;
}) {
  if (value == null) {
    return <span>Not enough history</span>;
  }

  const rounded = Number(value.toFixed(2));
  const cls =
    rounded > 0 ? "trend-up" : rounded < 0 ? "trend-down" : "trend-stable";
  const prefix = rounded > 0 ? "+" : "";

  return (
    <span className={`trend ${cls}`}>
      {prefix}
      {rounded}
      {unit}
      {" vs previous 30d"}
    </span>
  );
}

function MiniBarChart({
  title,
  points,
  color,
}: {
  title: string;
  points: ChartPoint[];
  color: string;
}) {
  const numericValues = points
    .map((point) => point.value)
    .filter((value): value is number => value != null);
  const max = numericValues.length > 0 ? Math.max(...numericValues) : 0;

  return (
    <div className="card">
      <div className="card-title" style={{ marginBottom: 16 }}>
        {title}
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: `repeat(${points.length}, minmax(0, 1fr))`,
          gap: 8,
          alignItems: "end",
          minHeight: 140,
        }}
      >
        {points.map((point) => {
          const value = point.value;
          const height =
            value == null || max === 0 ? 8 : Math.max(8, (value / max) * 110);

          return (
            <div
              key={point.date}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 8,
              }}
            >
              <div
                title={`${point.date}: ${value ?? "No data"}`}
                style={{
                  width: "100%",
                  height,
                  borderRadius: 999,
                  background:
                    value == null
                      ? "var(--border)"
                      : `linear-gradient(180deg, ${color}, rgba(255,255,255,0.12))`,
                  opacity: value == null ? 0.45 : 1,
                }}
              />
              <div
                style={{
                  fontSize: "0.68rem",
                  color: "var(--text-muted)",
                }}
              >
                {point.date.slice(5)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function InfoLine({
  label,
  value,
}: {
  label: string;
  value: string | number | null;
}) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        gap: 12,
        padding: "8px 0",
        borderBottom: "1px solid var(--border)",
      }}
    >
      <span style={{ color: "var(--text-secondary)" }}>{label}</span>
      <span style={{ color: "var(--text-primary)", fontWeight: 600 }}>
        {value ?? "N/A"}
      </span>
    </div>
  );
}

function AnalysisCard({
  title,
  analysis,
}: {
  title: string;
  analysis: IndicatorAnalysisPeriods | null | undefined;
}) {
  const hasAnalysis = Boolean(analysis?.["7d"] || analysis?.["30d"]);

  return (
    <div className="card">
      <div className="card-title" style={{ marginBottom: 12 }}>
        {title}
      </div>
      {hasAnalysis ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div>
            <div
              style={{
                fontSize: "0.76rem",
                color: "var(--text-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                marginBottom: 6,
              }}
            >
              7d
            </div>
            <div style={{ color: "var(--text-primary)", lineHeight: 1.6 }}>
              {analysis?.["7d"] ?? "No analysis yet"}
            </div>
          </div>
          <div>
            <div
              style={{
                fontSize: "0.76rem",
                color: "var(--text-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                marginBottom: 6,
              }}
            >
              30d
            </div>
            <div style={{ color: "var(--text-primary)", lineHeight: 1.6 }}>
              {analysis?.["30d"] ?? "No analysis yet"}
            </div>
          </div>
        </div>
      ) : (
        <div style={{ color: "var(--text-muted)" }}>
          No stored AI analysis yet
        </div>
      )}
    </div>
  );
}

function formatRange(start: string | null, end: string | null) {
  if (!start || !end) {
    return null;
  }
  return `${start} to ${end}`;
}

function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return null;
  }

  return new Date(value).toLocaleString();
}

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getStats(), getAlerts(true)])
      .then(([dashboardStats, dashboardAlerts]) => {
        setDashboard(dashboardStats);
        setAlerts(dashboardAlerts);
      })
      .catch((e) => setError(e.message ?? "Failed to load dashboard"))
      .finally(() => setLoading(false));
  }, []);

  const dismissAlert = async (id: number) => {
    await markAlertRead(id);
    setAlerts((prev) => prev.filter((alert) => alert.id !== id));
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
        <div className="empty-icon">!</div>
        <p>{error}</p>
        <p style={{ fontSize: "0.8rem", marginTop: 8 }}>
          Make sure the backend is running at localhost:8000
        </p>
      </div>
    );
  }

  const stats = dashboard?.stats;
  const analysis = dashboard?.analysis;
  const overallAnalysis = dashboard?.overall_analysis;

  const basic = stats?.basic;
  const diet = stats?.diet;
  const exercise = stats?.exercise;
  const sleep = stats?.sleep;
  const periodCycle = stats?.period_cycle;

  const hasAnyStats = Boolean(
    basic?.avg_weight_7d != null ||
      diet?.avg_calories_7d != null ||
      exercise?.avg_duration_7d != null ||
      sleep?.avg_sleep_duration_7d != null,
  );

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Live health statistics computed from your recent daily logs.</p>
      </div>

      <div className="card" style={{ marginBottom: 28 }}>
        <div className="card-title" style={{ marginBottom: 10 }}>
          Overall AI Summary
        </div>
        <div style={{ color: "var(--text-primary)", lineHeight: 1.7 }}>
          {overallAnalysis?.summary ?? "No overall analysis available yet."}
        </div>
        {overallAnalysis?.created_at && (
          <div
            style={{
              marginTop: 10,
              fontSize: "0.8rem",
              color: "var(--text-muted)",
            }}
          >
            Generated {formatDateTime(overallAnalysis.created_at)}
          </div>
        )}
      </div>

      {alerts.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 28 }}>
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`alert-banner ${alert.alert_type === "stale" ? "alert-banner-stale" : ""}`}
            >
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
                x
              </button>
            </div>
          ))}
        </div>
      )}

      <h3
        style={{
          color: "var(--text-secondary)",
          marginBottom: 12,
          fontSize: "0.85rem",
          textTransform: "uppercase",
          letterSpacing: "0.08em",
        }}
      >
        Basic
      </h3>
      <div className="stat-grid" style={{ marginBottom: 16 }}>
        <StatCard
          title="Average Weight 7d"
          value={basic?.avg_weight_7d ?? null}
          unit="kg"
          icon="BW"
          sub={<DeltaBadge value={basic?.weight_trend ?? null} unit=" kg" />}
        />
        <StatCard
          title="Average Weight 30d"
          value={basic?.avg_weight_30d ?? null}
          unit="kg"
          icon="30"
          sub={
            basic?.previous_avg_weight_30d != null
              ? `Previous 30d: ${basic.previous_avg_weight_30d} kg`
              : "Not enough history"
          }
        />
        <StatCard
          title="Latest Weight"
          value={basic?.latest_weight_kg ?? null}
          unit="kg"
          icon="KG"
        />
      </div>
      <MiniBarChart
        title="Weight Trend - Last 30 Days"
        points={basic?.bar_chart_data.last_30_days ?? []}
        color="var(--teal)"
      />
      <div className="grid-2" style={{ marginTop: 16 }}>
        <AnalysisCard title="Basic AI Analysis" analysis={analysis?.basic} />
      </div>

      <h3
        style={{
          color: "var(--text-secondary)",
          marginTop: 28,
          marginBottom: 12,
          fontSize: "0.85rem",
          textTransform: "uppercase",
          letterSpacing: "0.08em",
        }}
      >
        Diet
      </h3>
      <div className="stat-grid" style={{ marginBottom: 16 }}>
        <StatCard
          title="Average Calories 7d"
          value={diet?.avg_calories_7d ?? null}
          unit="kcal"
          icon="DI"
          sub={<DeltaBadge value={diet?.calories_trend ?? null} unit=" kcal" />}
        />
        <StatCard
          title="Average Protein 7d"
          value={diet?.avg_protein_g_7d ?? null}
          unit="g"
          icon="PR"
          sub={
            diet?.avg_protein_g_30d != null
              ? `30d average: ${diet.avg_protein_g_30d} g`
              : "No 30d average"
          }
        />
        <StatCard
          title="Average Carbs 7d"
          value={diet?.avg_carbs_g_7d ?? null}
          unit="g"
          icon="CB"
          sub={
            diet?.avg_fat_g_7d != null ? `Fat 7d: ${diet.avg_fat_g_7d} g` : "No fat data"
          }
        />
      </div>
      <MiniBarChart
        title="Calories - Last 7 Days"
        points={diet?.bar_chart_data.last_7_days ?? []}
        color="var(--amber)"
      />
      <div className="grid-2" style={{ marginTop: 16 }}>
        <AnalysisCard title="Diet AI Analysis" analysis={analysis?.diet} />
      </div>

      <h3
        style={{
          color: "var(--text-secondary)",
          marginTop: 28,
          marginBottom: 12,
          fontSize: "0.85rem",
          textTransform: "uppercase",
          letterSpacing: "0.08em",
        }}
      >
        Exercise
      </h3>
      <div className="stat-grid" style={{ marginBottom: 16 }}>
        <StatCard
          title="Average Duration 7d"
          value={exercise?.avg_duration_7d ?? null}
          unit="min"
          icon="EX"
          sub={<DeltaBadge value={exercise?.duration_trend ?? null} unit=" min" />}
        />
        <StatCard
          title="Average Duration 30d"
          value={exercise?.avg_duration_30d ?? null}
          unit="min"
          icon="30"
          sub={
            exercise?.previous_avg_duration_30d != null
              ? `Previous 30d: ${exercise.previous_avg_duration_30d} min`
              : "Not enough history"
          }
        />
        <StatCard
          title="Intensity Mix"
          value={null}
          icon="IX"
          sub={
            exercise
              ? `Low ${exercise.intensity_distribution.low} | Medium ${exercise.intensity_distribution.medium} | High ${exercise.intensity_distribution.high}`
              : "No exercise data"
          }
        />
      </div>
      <MiniBarChart
        title="Exercise Minutes - Last 30 Days"
        points={exercise?.bar_chart_data.last_30_days ?? []}
        color="var(--green)"
      />
      {exercise?.steps_bar_chart_7d && (
        <>
          <div className="stat-grid" style={{ marginTop: 16, marginBottom: 16 }}>
            <StatCard
              title="Total Steps (7d) ❤️"
              value={exercise.total_steps_7d?.toLocaleString() ?? null}
              icon="👟"
              sub="Apple Health"
            />
            <StatCard
              title="Avg Daily Steps ❤️"
              value={exercise.avg_daily_steps?.toLocaleString() ?? null}
              icon="🚶"
              sub="Apple Health"
            />
          </div>
          <MiniBarChart
            title="Daily Steps - Last 7 Days (Apple Health ❤️)"
            points={exercise.steps_bar_chart_7d}
            color="var(--teal)"
          />
        </>
      )}
      <div className="grid-2" style={{ marginTop: 16 }}>
        <AnalysisCard title="Exercise AI Analysis" analysis={analysis?.exercise} />
      </div>

      <h3
        style={{
          color: "var(--text-secondary)",
          marginTop: 28,
          marginBottom: 12,
          fontSize: "0.85rem",
          textTransform: "uppercase",
          letterSpacing: "0.08em",
        }}
      >
        Sleep
      </h3>
      <div className="stat-grid" style={{ marginBottom: 16 }}>
        <StatCard
          title="Average Sleep 7d"
          value={sleep?.avg_sleep_duration_7d ?? null}
          unit="hrs"
          icon="SL"
          sub={<DeltaBadge value={sleep?.sleep_trend ?? null} unit=" hrs" />}
        />
        <StatCard
          title="Average Sleep 30d"
          value={sleep?.avg_sleep_duration_30d ?? null}
          unit="hrs"
          icon="30"
          sub={
            sleep?.previous_avg_sleep_duration_30d != null
              ? `Previous 30d: ${sleep.previous_avg_sleep_duration_30d} hrs`
              : "Not enough history"
          }
        />
        <StatCard
          title="Average Quality"
          value={sleep?.avg_quality_7d ?? null}
          unit="/5"
          icon="QL"
          sub={
            sleep?.avg_quality_30d != null
              ? `30d average: ${sleep.avg_quality_30d}/5`
              : "No 30d quality data"
          }
        />
      </div>
      <MiniBarChart
        title="Sleep Hours - Last 7 Days"
        points={sleep?.bar_chart_data.last_7_days ?? []}
        color="var(--accent)"
      />
      <div className="grid-2" style={{ marginTop: 16 }}>
        <AnalysisCard title="Sleep AI Analysis" analysis={analysis?.sleep} />
      </div>

      <h3
        style={{
          color: "var(--text-secondary)",
          marginTop: 28,
          marginBottom: 12,
          fontSize: "0.85rem",
          textTransform: "uppercase",
          letterSpacing: "0.08em",
        }}
      >
        Period Cycle
      </h3>
      <div className="grid-2" style={{ marginBottom: 28 }}>
        <div className="card">
          <div className="card-title" style={{ marginBottom: 8 }}>
            Cycle Summary
          </div>
          <InfoLine
            label="Last cycle"
            value={formatRange(periodCycle?.last_cycle_start ?? null, periodCycle?.last_cycle_end ?? null)}
          />
          <InfoLine
            label="Average cycle length"
            value={
              periodCycle?.avg_cycle_length_days != null
                ? `${periodCycle.avg_cycle_length_days} days`
                : null
            }
          />
          <InfoLine
            label="Predicted next start"
            value={formatRange(
              periodCycle?.predicted_next_start_start ?? null,
              periodCycle?.predicted_next_start_end ?? null,
            )}
          />
        </div>
      </div>

      {!hasAnyStats && (
        <div className="card" style={{ textAlign: "center", marginTop: 40 }}>
          <div style={{ fontSize: "3rem", marginBottom: 16 }}>...</div>
          <h3>No health data yet</h3>
          <p style={{ marginTop: 8, marginBottom: 20 }}>
            Start logging your daily metrics to unlock the new dashboard analysis.
          </p>
          <a href="/questionnaire" className="btn btn-primary">
            Log My First Entry
          </a>
        </div>
      )}
    </div>
  );
}
