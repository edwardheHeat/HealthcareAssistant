"use client";

import AlertCard from "./AlertCard";
import type { Alert } from "@/types/stats";

interface NotificationPanelProps {
  alerts: Alert[];
  onClose: () => void;
  onDelete: (id: number) => void;
  onDismiss: (id: number) => void;
  onDeleteDay: (dateKey: string) => void;
  onDeleteAll: () => void;
}

function toLocalDateKey(isoString: string): string {
  // Convert UTC ISO string to YYYY-MM-DD in the user's local timezone
  return new Date(isoString).toLocaleDateString("en-CA"); // en-CA gives YYYY-MM-DD
}

function friendlyDateLabel(dateKey: string): string {
  const today = new Date().toLocaleDateString("en-CA");
  const yesterday = new Date(Date.now() - 86_400_000).toLocaleDateString("en-CA");
  if (dateKey === today) return "Today";
  if (dateKey === yesterday) return "Yesterday";
  return new Date(dateKey + "T12:00:00").toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

export default function NotificationPanel({
  alerts,
  onClose,
  onDelete,
  onDismiss,
  onDeleteDay,
  onDeleteAll,
}: NotificationPanelProps) {
  // Group alerts by local calendar date
  const grouped = alerts.reduce<Record<string, Alert[]>>((acc, alert) => {
    const key = toLocalDateKey(alert.created_at);
    (acc[key] ??= []).push(alert);
    return acc;
  }, {});

  const dateKeys = Object.keys(grouped).sort((a, b) => (a > b ? -1 : 1));

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 40,
          background: "rgba(0,0,0,0.3)",
          backdropFilter: "blur(2px)",
        }}
      />

      {/* Panel */}
      <div
        style={{
          position: "fixed",
          top: 0,
          right: 0,
          bottom: 0,
          width: 400,
          maxWidth: "92vw",
          zIndex: 50,
          background: "var(--bg-surface)",
          borderLeft: "1px solid var(--border)",
          display: "flex",
          flexDirection: "column",
          boxShadow: "var(--shadow-elevated)",
          animation: "slideIn 0.22s ease",
        }}
      >
        <style>{`
          @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to   { transform: translateX(0);    opacity: 1; }
          }
        `}</style>

        {/* Header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "16px 20px",
            borderBottom: "1px solid var(--border)",
            flexShrink: 0,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: "1.2rem" }}>🔔</span>
            <h3 style={{ fontSize: "1rem", fontWeight: 600 }}>Notifications</h3>
            {alerts.filter((a) => !a.is_read).length > 0 && (
              <span
                className="badge badge-rose"
                style={{ fontSize: "0.7rem", padding: "2px 8px" }}
              >
                {alerts.filter((a) => !a.is_read).length} new
              </span>
            )}
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            {alerts.length > 0 && (
              <button
                onClick={onDeleteAll}
                className="btn btn-ghost"
                style={{ fontSize: "0.78rem", padding: "5px 12px", color: "var(--rose)" }}
              >
                Delete All
              </button>
            )}
            <button
              onClick={onClose}
              style={{
                background: "none",
                border: "none",
                cursor: "pointer",
                color: "var(--text-muted)",
                fontSize: "1.1rem",
                padding: "4px 8px",
              }}
            >
              ✕
            </button>
          </div>
        </div>

        {/* Content */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "16px 20px",
            display: "flex",
            flexDirection: "column",
            gap: 24,
          }}
        >
          {alerts.length === 0 ? (
            <div className="empty-state" style={{ paddingTop: 60 }}>
              <div className="empty-icon">✅</div>
              <h3>All clear!</h3>
              <p style={{ marginTop: 8 }}>No health alerts at this time.</p>
            </div>
          ) : (
            dateKeys.map((dateKey) => (
              <div key={dateKey}>
                {/* Day header */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginBottom: 10,
                  }}
                >
                  <span
                    style={{
                      fontSize: "0.78rem",
                      fontWeight: 700,
                      textTransform: "uppercase",
                      letterSpacing: "0.07em",
                      color: "var(--text-muted)",
                    }}
                  >
                    {friendlyDateLabel(dateKey)}
                  </span>
                  <button
                    onClick={() => onDeleteDay(dateKey)}
                    className="btn btn-ghost"
                    style={{
                      fontSize: "0.72rem",
                      padding: "3px 10px",
                      color: "var(--text-muted)",
                    }}
                  >
                    Delete Day
                  </button>
                </div>

                {/* Alert cards */}
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {grouped[dateKey].map((alert) => (
                    <AlertCard
                      key={alert.id}
                      alert={alert}
                      onDelete={onDelete}
                      onDismiss={onDismiss}
                    />
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </>
  );
}
