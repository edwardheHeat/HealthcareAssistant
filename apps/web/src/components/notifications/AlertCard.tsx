"use client";

import type { Alert } from "@/types/stats";
import { useRouter } from "next/navigation";

interface AlertCardProps {
  alert: Alert;
  onDelete: (id: number) => void;
  onDismiss: (id: number) => void;
}

const SEVERITY_CONFIG = {
  critical: { icon: "🔴", color: "var(--rose)", bg: "var(--rose-soft)" },
  warning: { icon: "🟡", color: "var(--amber)", bg: "var(--amber-soft)" },
};

const METRIC_LABELS: Record<string, string> = {
  basic_indicators: "Body Metrics",
  diet: "Diet",
  sleep: "Sleep",
  calories: "Calories",
  bmi: "BMI",
  exercise: "Exercise",
  period: "Cycle",
};

export default function AlertCard({ alert, onDelete, onDismiss }: AlertCardProps) {
  const router = useRouter();
  const cfg = SEVERITY_CONFIG[alert.severity] ?? SEVERITY_CONFIG.warning;
  const metricLabel = METRIC_LABELS[alert.metric] ?? alert.metric;

  const handleAskLlm = () => {
    const prompt = encodeURIComponent(`Tell me more about this health alert: ${alert.message}`);
    // Mark as read, then navigate to chat with pre-filled prompt
    onDismiss(alert.id);
    router.push(`/chat?prompt=${prompt}`);
  };

  return (
    <div
      style={{
        background: alert.is_read ? "var(--bg-elevated)" : cfg.bg,
        border: `1px solid ${alert.is_read ? "var(--border)" : cfg.color}`,
        borderRadius: "var(--radius-md)",
        padding: "12px 14px",
        opacity: alert.is_read ? 0.7 : 1,
        transition: "all 0.2s ease",
      }}
    >
      {/* Header row */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          marginBottom: 6,
        }}
      >
        <span style={{ fontSize: "0.95rem" }}>{cfg.icon}</span>
        <span
          style={{
            fontSize: "0.72rem",
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.07em",
            color: cfg.color,
          }}
        >
          {alert.severity}
        </span>
        <span
          style={{
            fontSize: "0.72rem",
            color: "var(--text-muted)",
            marginLeft: 2,
          }}
        >
          · {metricLabel}
        </span>
        {!alert.is_read && (
          <span
            style={{
              marginLeft: "auto",
              width: 7,
              height: 7,
              background: cfg.color,
              borderRadius: "50%",
              flexShrink: 0,
            }}
          />
        )}
      </div>

      {/* Message */}
      <p
        style={{
          fontSize: "0.85rem",
          color: "var(--text-primary)",
          lineHeight: 1.5,
          marginBottom: 10,
        }}
      >
        {alert.message}
      </p>

      {/* Actions */}
      <div style={{ display: "flex", gap: 8 }}>
        <button
          onClick={handleAskLlm}
          className="btn btn-ghost"
          style={{ fontSize: "0.78rem", padding: "5px 12px" }}
        >
          💬 Ask LLM
        </button>
        <button
          onClick={() => onDelete(alert.id)}
          className="btn btn-ghost"
          style={{
            fontSize: "0.78rem",
            padding: "5px 10px",
            color: "var(--rose)",
            borderColor: "transparent",
          }}
        >
          ✕
        </button>
      </div>
    </div>
  );
}
