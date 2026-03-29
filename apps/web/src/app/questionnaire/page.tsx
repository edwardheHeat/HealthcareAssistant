"use client";

import { useState } from "react";
import {
  postBasicIndicators,
  postDiet,
  postSleep,
  postExercise,
  postPeriod,
} from "@/lib/apiClient";
import type { WorkActivityLevel, ExerciseIntensity, FlowAmount } from "@/types/health";

type TabId = "basic" | "diet" | "sleep" | "exercise" | "clinical" | "period";

const TABS: { id: TabId; label: string; icon: string }[] = [
  { id: "basic", label: "Body", icon: "⚖️" },
  { id: "diet", label: "Diet", icon: "🍽️" },
  { id: "sleep", label: "Sleep", icon: "😴" },
  { id: "exercise", label: "Exercise", icon: "🏃" },
  { id: "period", label: "Cycle", icon: "🌙" },
];

function SuccessBanner({ message, onClose }: { message: string; onClose: () => void }) {
  return (
    <div
      style={{
        background: "var(--green-soft)",
        border: "1px solid var(--green)",
        borderRadius: "var(--radius-md)",
        padding: "12px 16px",
        display: "flex",
        alignItems: "center",
        gap: 10,
        color: "var(--green)",
        marginBottom: 20,
        fontSize: "0.9rem",
        fontWeight: 500,
      }}
    >
      <span>✓</span>
      <span style={{ flex: 1 }}>{message}</span>
      <button
        onClick={onClose}
        style={{
          background: "none",
          border: "none",
          cursor: "pointer",
          color: "inherit",
          fontSize: "1rem",
        }}
      >
        ✕
      </button>
    </div>
  );
}

// =========================================================================== //
// BASIC INDICATORS                                                             //
// =========================================================================== //
function BasicSection({ onSuccess }: { onSuccess: (msg: string) => void }) {
  const [height, setHeight] = useState("");
  const [weight, setWeight] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const submit = async () => {
    setErr(null);
    if (!height || !weight) { setErr("All fields are required."); return; }
    setLoading(true);
    try {
      await postBasicIndicators({ height_ft: parseFloat(height), weight_lbs: parseFloat(weight) });
      onSuccess("Body metrics saved successfully!");
      setHeight(""); setWeight("");
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-section">
      {err && <div className="alert-banner">{err}</div>}
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Height (ft)</label>
          <input className="form-input" type="number" step="0.1" placeholder="e.g. 5.8" value={height} onChange={(e) => setHeight(e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label">Weight (lbs)</label>
          <input className="form-input" type="number" step="0.1" placeholder="e.g. 150" value={weight} onChange={(e) => setWeight(e.target.value)} />
        </div>
      </div>
      <button className="btn btn-primary" onClick={submit} disabled={loading}>
        {loading ? "Saving…" : "Save Body Metrics"}
      </button>
    </div>
  );
}

// =========================================================================== //
// DIET                                                                         //
// =========================================================================== //
function DietSection({ onSuccess }: { onSuccess: (msg: string) => void }) {
  const [calories, setCalories] = useState("");
  const [protein, setProtein] = useState("");
  const [carbs, setCarbs] = useState("");
  const [fat, setFat] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const submit = async () => {
    setErr(null);
    if (!calories) { setErr("Calorie intake is required."); return; }
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append("calorie_intake", calories);
      if (protein) fd.append("protein_g", protein);
      if (carbs) fd.append("carbs_g", carbs);
      if (fat) fd.append("fat_g", fat);
      if (image) fd.append("food_image", image);
      await postDiet(fd);
      onSuccess("Diet entry saved!");
      setCalories(""); setProtein(""); setCarbs(""); setFat(""); setImage(null);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-section">
      {err && <div className="alert-banner">{err}</div>}
      <div className="form-group">
        <label className="form-label">Calorie Intake (kcal) *</label>
        <input className="form-input" type="number" placeholder="e.g. 2000" value={calories} onChange={(e) => setCalories(e.target.value)} />
      </div>
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Protein (g)</label>
          <input className="form-input" type="number" placeholder="e.g. 80" value={protein} onChange={(e) => setProtein(e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label">Carbs (g)</label>
          <input className="form-input" type="number" placeholder="e.g. 250" value={carbs} onChange={(e) => setCarbs(e.target.value)} />
        </div>
      </div>
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Fat (g)</label>
          <input className="form-input" type="number" placeholder="e.g. 60" value={fat} onChange={(e) => setFat(e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label">Food Photo (optional)</label>
          <input
            className="form-input"
            type="file"
            accept="image/*"
            onChange={(e) => setImage(e.target.files?.[0] ?? null)}
            style={{ padding: "6px 14px", cursor: "pointer" }}
          />
        </div>
      </div>
      {image && (
        <div style={{ fontSize: "0.82rem", color: "var(--teal)" }}>
          📷 {image.name} selected
        </div>
      )}
      <button className="btn btn-primary" onClick={submit} disabled={loading}>
        {loading ? "Saving…" : "Save Diet Entry"}
      </button>
    </div>
  );
}

// =========================================================================== //
// SLEEP                                                                        //
// =========================================================================== //
function SleepSection({ onSuccess }: { onSuccess: (msg: string) => void }) {
  const [sleepStart, setSleepStart] = useState("");
  const [wakeTime, setWakeTime] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const submit = async () => {
    setErr(null);
    if (!sleepStart || !wakeTime) { setErr("Both sleep and wake times are required."); return; }
    setLoading(true);
    try {
      await postSleep({ sleep_start: sleepStart, wake_time: wakeTime });
      onSuccess("Sleep record saved!");
      setSleepStart(""); setWakeTime("");
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-section">
      {err && <div className="alert-banner">{err}</div>}
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Sleep Start Time</label>
          <input className="form-input" type="datetime-local" value={sleepStart} onChange={(e) => setSleepStart(e.target.value)} style={{ colorScheme: "dark" }} />
        </div>
        <div className="form-group">
          <label className="form-label">Wake Up Time</label>
          <input className="form-input" type="datetime-local" value={wakeTime} onChange={(e) => setWakeTime(e.target.value)} style={{ colorScheme: "dark" }} />
        </div>
      </div>
      {sleepStart && wakeTime && new Date(wakeTime) > new Date(sleepStart) && (
        <div style={{ color: "var(--teal)", fontSize: "0.85rem" }}>
          ✓ Duration:{" "}
          {(
            (new Date(wakeTime).getTime() - new Date(sleepStart).getTime()) /
            3600000
          ).toFixed(1)}{" "}
          hours
        </div>
      )}
      <button className="btn btn-primary" onClick={submit} disabled={loading}>
        {loading ? "Saving…" : "Save Sleep Record"}
      </button>
    </div>
  );
}

// =========================================================================== //
// EXERCISE                                                                     //
// =========================================================================== //
function ExerciseSection({ onSuccess }: { onSuccess: (msg: string) => void }) {
  const [workLevel, setWorkLevel] = useState<WorkActivityLevel>("sedentary");
  const [type, setType] = useState("");
  const [intensity, setIntensity] = useState<ExerciseIntensity>("moderate");
  const [duration, setDuration] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const submit = async () => {
    setErr(null);
    if (!type || !duration) { setErr("Exercise type and duration are required."); return; }
    setLoading(true);
    try {
      const result = await postExercise({
        work_activity_level: workLevel,
        exercise_type: type,
        exercise_intensity: intensity,
        duration_min: parseInt(duration),
      });
      onSuccess(`Exercise saved! Computed MET: ${result.met_value}`);
      setType(""); setDuration("");
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-section">
      {err && <div className="alert-banner">{err}</div>}
      <div className="form-group">
        <label className="form-label">Occupational Activity Level</label>
        <select className="form-select" value={workLevel} onChange={(e) => setWorkLevel(e.target.value as WorkActivityLevel)}>
          <option value="sedentary">Sedentary (desk job)</option>
          <option value="light">Light (teacher, light walking)</option>
          <option value="moderate">Moderate (nurse, retail)</option>
          <option value="heavy">Heavy (construction)</option>
          <option value="very_heavy">Very Heavy (elite athlete)</option>
        </select>
      </div>
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Exercise Type</label>
          <input className="form-input" type="text" placeholder="e.g. running, cycling, yoga" value={type} onChange={(e) => setType(e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label">Intensity</label>
          <select className="form-select" value={intensity} onChange={(e) => setIntensity(e.target.value as ExerciseIntensity)}>
            <option value="low">Low</option>
            <option value="moderate">Moderate</option>
            <option value="high">High</option>
            <option value="very_high">Very High</option>
          </select>
        </div>
      </div>
      <div className="form-group">
        <label className="form-label">Duration (minutes)</label>
        <input className="form-input" type="number" placeholder="e.g. 45" value={duration} onChange={(e) => setDuration(e.target.value)} />
      </div>
      <button className="btn btn-primary" onClick={submit} disabled={loading}>
        {loading ? "Calculating MET…" : "Save Exercise"}
      </button>
    </div>
  );
}

// =========================================================================== //
// PERIOD                                                                       //
// =========================================================================== //
function PeriodSection({ onSuccess }: { onSuccess: (msg: string) => void }) {
  const [hasFlow, setHasFlow] = useState(false);
  const [flowAmount, setFlowAmount] = useState<FlowAmount | "">("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const submit = async () => {
    setErr(null);
    setLoading(true);
    try {
      await postPeriod({ has_flow: hasFlow, flow_amount: hasFlow && flowAmount ? flowAmount : null });
      onSuccess("Cycle data saved!");
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-section">
      {err && <div className="alert-banner">{err}</div>}
      <div className="form-group">
        <label className="form-label">Flow Today?</label>
        <div style={{ display: "flex", gap: 12, marginTop: 4 }}>
          {[true, false].map((val) => (
            <button
              key={String(val)}
              onClick={() => setHasFlow(val)}
              className={`btn ${hasFlow === val ? "btn-primary" : "btn-ghost"}`}
            >
              {val ? "Yes" : "No"}
            </button>
          ))}
        </div>
      </div>
      {hasFlow && (
        <div className="form-group">
          <label className="form-label">Flow Amount</label>
          <select className="form-select" value={flowAmount} onChange={(e) => setFlowAmount(e.target.value as FlowAmount)}>
            <option value="">Select…</option>
            <option value="light">Light</option>
            <option value="medium">Medium</option>
            <option value="heavy">Heavy</option>
          </select>
        </div>
      )}
      <button className="btn btn-primary" onClick={submit} disabled={loading}>
        {loading ? "Saving…" : "Save Cycle Data"}
      </button>
    </div>
  );
}

// =========================================================================== //
// PAGE                                                                          //
// =========================================================================== //
export default function QuestionnairePage() {
  const [activeTab, setActiveTab] = useState<TabId>("basic");
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleSuccess = (msg: string) => {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(null), 4000);
  };

  const sectionProps = { onSuccess: handleSuccess };

  return (
    <div>
      <div className="page-header">
        <h1>Log Health Data</h1>
        <p>Record your daily metrics — each section is saved independently</p>
      </div>

      {successMsg && (
        <SuccessBanner message={successMsg} onClose={() => setSuccessMsg(null)} />
      )}

      <div className="tabs" style={{ marginBottom: 28 }}>
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`tab ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      <div className="card" style={{ maxWidth: 640 }}>
        {activeTab === "basic" && <BasicSection {...sectionProps} />}
        {activeTab === "diet" && <DietSection {...sectionProps} />}
        {activeTab === "sleep" && <SleepSection {...sectionProps} />}
        {activeTab === "exercise" && <ExerciseSection {...sectionProps} />}
        {activeTab === "period" && <PeriodSection {...sectionProps} />}
      </div>
    </div>
  );
}
