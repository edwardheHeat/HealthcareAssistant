"use client";

/**
 * Apple Health Import Page
 *
 * Supports two import modes:
 * 1. Mock sync: Simulates 7 days of Apple Health data for demo
 * 2. Real export: Parses the actual Apple Health export.xml for 30 days of real data
 */

import { useRef, useState } from "react";
import { askHealthAI, generateHealthInsight, syncAppleHealth, parseAppleHealthExport } from "@/lib/apiClient";

// Mock data for demo
const MOCK_STEPS = [5200, 6100, 4800, 7000, 8200, 3000, 4500];
const MOCK_SLEEP = [7.5, 6.8, 6.2, 5.9, 6.0, 7.8, 8.1];
const DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

type SyncStage = "idle" | "connecting" | "permission" | "importing" | "done";

interface SyncStageInfo {
  icon: string;
  text: string;
  sub: string;
}

const STAGE_INFO: Record<SyncStage, SyncStageInfo> = {
  idle: { icon: "", text: "", sub: "" },
  connecting: {
    icon: "📡",
    text: "Connecting to Apple Health...",
    sub: "Establishing secure HealthKit connection",
  },
  permission: {
    icon: "🔐",
    text: "Requesting permission...",
    sub: "Asking for read access to steps and sleep data",
  },
  importing: {
    icon: "⬇️",
    text: "Importing health data...",
    sub: "Fetching last 7 days of steps and sleep records",
  },
  done: {
    icon: "✅",
    text: "Sync complete",
    sub: "Your Apple Health data has been imported",
  },
};

type ExportStage = "idle" | "parsing" | "done" | "error";

function SyncStatusCard({ stage }: { stage: SyncStage }) {
  const info = STAGE_INFO[stage];
  return (
    <div className="ah-status-card" style={{ marginBottom: 24 }}>
      <div className="ah-status-icon">{info.icon}</div>
      <div>
        <div className="ah-status-text">{info.text}</div>
        <div className="ah-status-sub">{info.sub}</div>
      </div>
      {stage !== "done" && (
        <div className="spinner" style={{ marginTop: 8 }} />
      )}
    </div>
  );
}

function MiniBarChart({
  values,
  labels,
  color,
  unit,
}: {
  values: number[];
  labels: string[];
  color: string;
  unit: string;
}) {
  const max = Math.max(...values);
  return (
    <div className="ah-bar-chart">
      {values.map((v, i) => {
        const heightPct = max > 0 ? (v / max) * 100 : 0;
        return (
          <div key={labels[i]} className="ah-bar-col">
            <div
              style={{
                fontSize: "0.68rem",
                color: "var(--text-muted)",
                marginBottom: 2,
              }}
            >
              {unit === "k" ? (v / 1000).toFixed(1) + "k" : v + unit}
            </div>
            <div
              className="ah-bar"
              style={{
                height: `${Math.max(4, heightPct)}px`,
                background: `linear-gradient(180deg, ${color}, rgba(255,255,255,0.1))`,
              }}
            />
            <div className="ah-bar-label">{labels[i]}</div>
          </div>
        );
      })}
    </div>
  );
}

function SummaryChip({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 2,
        padding: "10px 16px",
        background: "var(--bg-elevated)",
        borderRadius: "var(--radius-md)",
        border: "1px solid var(--border)",
        minWidth: 110,
      }}
    >
      <div
        style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}
      >
        {label}
      </div>
      <div style={{ fontSize: "1.2rem", fontWeight: 700, color }}>{value}</div>
    </div>
  );
}

export default function AppleHealthPage() {
  const [syncStage, setSyncStage] = useState<SyncStage>("idle");
  const [synced, setSynced] = useState(false);
  const [insight, setInsight] = useState<string | null>(null);
  const [insightLoading, setInsightLoading] = useState(false);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [askLoading, setAskLoading] = useState(false);
  const [askError, setAskError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Real export import state
  const [exportStage, setExportStage] = useState<ExportStage>("idle");
  const [exportError, setExportError] = useState<string | null>(null);
  const [exportData, setExportData] = useState<Record<string, unknown> | null>(null);

  async function handleSync() {
    setSyncStage("connecting");
    await delay(1200);
    setSyncStage("permission");
    await delay(1400);
    setSyncStage("importing");
    await delay(1600);
    try {
      await syncAppleHealth({ steps: MOCK_STEPS, sleep: MOCK_SLEEP });
    } catch {
      // Non-fatal
    }
    setSyncStage("done");
    await delay(800);
    setSynced(true);
    fetchInsight();
  }

  async function handleParseExport() {
    setExportStage("parsing");
    setExportError(null);
    try {
      const result = await parseAppleHealthExport();
      setExportData(result);
      setExportStage("done");
    } catch (e: unknown) {
      setExportError(e instanceof Error ? e.message : "Failed to parse export");
      setExportStage("error");
    }
  }

  async function fetchInsight() {
    setInsightLoading(true);
    try {
      const res = await generateHealthInsight({ steps: MOCK_STEPS, sleep: MOCK_SLEEP });
      setInsight(res.insight);
    } catch {
      setInsight(null);
    } finally {
      setInsightLoading(false);
    }
  }

  async function handleAsk() {
    if (!question.trim()) return;
    setAskLoading(true);
    setAnswer(null);
    setAskError(null);
    try {
      const res = await askHealthAI({
        question: question.trim(),
        steps: MOCK_STEPS,
        sleep: MOCK_SLEEP,
      });
      setAnswer(res.answer);
    } catch (e: unknown) {
      setAskError(e instanceof Error ? e.message : "Failed to get answer");
    } finally {
      setAskLoading(false);
    }
  }

  const totalSteps = MOCK_STEPS.reduce((a, b) => a + b, 0);
  const avgSleep = (MOCK_SLEEP.reduce((a, b) => a + b, 0) / MOCK_SLEEP.length).toFixed(1);
  const avgSteps = Math.round(totalSteps / MOCK_STEPS.length);

  return (
    <div>
      <div className="page-header">
        <h1>Apple Health</h1>
        <p>Import your health data and get AI-powered insights from your activity and sleep patterns.</p>
      </div>

      {/* ===== REAL EXPORT IMPORT SECTION ===== */}
      <div className="card" style={{ marginBottom: 24, borderLeft: "4px solid var(--accent)" }}>
        <div className="card-title" style={{ marginBottom: 12, color: "var(--accent)" }}>
          📊 Import Real Apple Health Data
        </div>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", marginBottom: 12 }}>
          Parse your real Apple Health export.zip file (30 days of steps, workouts, and more)
        </p>
        {exportStage === "idle" && (
          <button
            className="ah-sync-btn"
            onClick={handleParseExport}
            style={{ marginBottom: 8 }}
          >
            <span style={{ fontSize: "1.1rem" }}>📁</span>
            Parse export.zip from Project Root
          </button>
        )}
        {exportStage === "parsing" && (
          <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px" }}>
            <div className="spinner" />
            <span style={{ color: "var(--text-muted)" }}>
              Parsing 500k+ health records (this may take 30-60 seconds)...
            </span>
          </div>
        )}
        {exportStage === "done" && exportData && (
          <div style={{ backgroundColor: "rgba(52, 211, 153, 0.08)", padding: 12, borderRadius: 8 }}>
            <div style={{ color: "var(--green)", fontWeight: 600, marginBottom: 8 }}>✅ Export parsed successfully!</div>
            <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
              <div>📅 Date range: {exportData.date_range?.start ?? "?"} to {exportData.date_range?.end ?? "?"}</div>
              <div>📈 Totals: {JSON.stringify(exportData.totals).substring(0, 120)}...</div>
            </div>
          </div>
        )}
        {exportStage === "error" && (
          <div style={{ color: "var(--rose)", fontSize: "0.9rem", padding: "10px", backgroundColor: "rgba(244, 63, 94, 0.1)", borderRadius: 8 }}>
            ❌ {exportError}
          </div>
        )}
      </div>

      {/* ===== MOCK SYNC SECTION ===== */}
      {!synced && syncStage === "idle" && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 20,
              padding: "16px 0",
            }}
          >
            <div
              style={{
                width: 80,
                height: 80,
                borderRadius: "50%",
                background: "rgba(255,55,95,0.1)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "2.4rem",
              }}
            >
              ❤️
            </div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>
                Connect Apple Health (Mock Demo)
              </div>
              <div style={{ fontSize: "0.88rem", color: "var(--text-muted)", maxWidth: 340 }}>
                Simulate importing 7 days of steps and sleep data for demonstration.
              </div>
            </div>
            <button className="ah-sync-btn" style={{ maxWidth: 320 }} onClick={handleSync}>
              <span style={{ fontSize: "1.2rem" }}>❤️</span>
              Sync Mock Data
            </button>
            <div
              style={{
                fontSize: "0.75rem",
                color: "var(--text-muted)",
                textAlign: "center",
                maxWidth: 320,
                lineHeight: 1.5,
              }}
            >
              This simulates the Apple Health import flow. Use "Parse export.zip from Project Root" above for real data.
            </div>
          </div>
        </div>
      )}

      {!synced && syncStage !== "idle" && (
        <SyncStatusCard stage={syncStage} />
      )}

      {synced && (
        <>
          {/* Re-sync button */}
          <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 20 }}>
            <button
              className="ah-sync-btn ah-sync-btn-done"
              style={{ width: "auto", padding: "10px 20px", fontSize: "0.88rem" }}
              onClick={() => {
                setSynced(false);
                setSyncStage("idle");
                setInsight(null);
                setAnswer(null);
              }}
            >
              <span>✅</span>
              Synced · Re-import
            </button>
          </div>

          {/* Summary chips */}
          <div
            style={{
              display: "flex",
              gap: 12,
              flexWrap: "wrap",
              marginBottom: 24,
            }}
          >
            <SummaryChip
              label="Total Steps (7d)"
              value={totalSteps.toLocaleString()}
              color="var(--teal)"
            />
            <SummaryChip
              label="Avg Daily Steps"
              value={avgSteps.toLocaleString()}
              color="var(--green)"
            />
            <SummaryChip
              label="Avg Sleep"
              value={`${avgSleep} hrs`}
              color="var(--accent)"
            />
          </div>

          {/* Steps chart */}
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-title" style={{ marginBottom: 16 }}>
              Daily Steps — Last 7 Days
            </div>
            <MiniBarChart
              values={MOCK_STEPS}
              labels={DAY_LABELS}
              color="var(--teal)"
              unit="k"
            />
          </div>

          {/* Sleep chart */}
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="card-title" style={{ marginBottom: 16 }}>
              Sleep Duration — Last 7 Days
            </div>
            <MiniBarChart
              values={MOCK_SLEEP}
              labels={DAY_LABELS}
              color="var(--accent)"
              unit=" h"
            />
          </div>

          {/* AI Insight */}
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="card-title" style={{ marginBottom: 12 }}>
              Weekly AI Insight
            </div>
            {insightLoading ? (
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div className="spinner" />
                <span style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
                  Generating insight from your health data...
                </span>
              </div>
            ) : insight ? (
              <div
                style={{
                  color: "var(--text-primary)",
                  lineHeight: 1.7,
                  fontSize: "0.95rem",
                }}
              >
                {insight}
              </div>
            ) : (
              <div style={{ color: "var(--text-muted)" }}>
                Could not generate insight — check backend connection.
              </div>
            )}
          </div>

          {/* Ask AI */}
          <div className="card">
            <div className="card-title" style={{ marginBottom: 12 }}>
              Ask AI About Your Data
            </div>
            <div style={{ display: "flex", gap: 10, marginBottom: 4 }}>
              <input
                ref={inputRef}
                className="ah-ask-input"
                type="text"
                placeholder="e.g. Why do I feel tired mid-week?"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !askLoading) handleAsk();
                }}
                disabled={askLoading}
              />
              <button
                className="btn btn-primary"
                onClick={handleAsk}
                disabled={askLoading || !question.trim()}
              >
                {askLoading ? <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> : "Ask"}
              </button>
            </div>
            <div
              style={{
                fontSize: "0.75rem",
                color: "var(--text-muted)",
                marginBottom: answer || askError ? 12 : 0,
              }}
            >
              Your step and sleep data will be sent with your question.
            </div>

            {askError && (
              <div
                style={{
                  color: "var(--rose)",
                  fontSize: "0.88rem",
                  padding: "10px 14px",
                  background: "var(--rose-soft)",
                  borderRadius: "var(--radius-md)",
                  marginTop: 8,
                }}
              >
                {askError}
              </div>
            )}

            {answer && (
              <div className="ah-answer-bubble">
                <div
                  style={{
                    fontSize: "0.72rem",
                    fontWeight: 600,
                    color: "var(--accent)",
                    textTransform: "uppercase",
                    letterSpacing: "0.08em",
                    marginBottom: 8,
                  }}
                >
                  AI Response
                </div>
                {answer}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function delay(ms: number): Promise<void> {
  return new Promise((res) => setTimeout(res, ms));
}
