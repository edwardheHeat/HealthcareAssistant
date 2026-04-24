"""LLM prompt templates and context builder."""

import json
from collections.abc import Sequence
from typing import Any

from app.models.medical import ClinicalHistoryEntry
from app.models.user import UserProfile

_SYSTEM_TEMPLATE = """\
You are a compassionate and knowledgeable personal health assistant.
You have access to the user's health profile and recent statistics (provided below).
Your role is to:
- Answer health-related questions using the user's personal data as context.
- Help narrow down causes of symptoms (provide at most 3 possibilities).
- Recommend when to seek professional medical care.
- Respect relevant medical history and medication context.

You must NOT diagnose, prescribe medication, or replace a healthcare provider.
Always be supportive, clear, and non-alarmist. Ask clarifying follow-up questions
when needed to better understand the user's situation.

---
## User Profile
Name: {name}
Age: {age}
Sex: {sex}

---
## Current Health Statistics
{stats_summary}

---
## Apple Health Data (imported via HealthKit)
{apple_health_summary}

---
## Clinical History
{clinical_summary}
---
"""


def _format_stats(stats: dict) -> str:
    lines: list[str] = []

    if stats.get("bmi"):
        lines.append(
            "- BMI: "
            f"{stats['bmi']} "
            f"(weight trend: {stats.get('weight_trend', 'unknown')})"
        )

    if stats.get("current_weight_kg") is not None:
        lines.append(
            f"- Weight: {stats['current_weight_kg']} kg | "
            f"Height: {stats.get('current_height_cm')} cm"
        )
    elif stats.get("current_weight_lbs") is not None:
        lines.append(
            f"- Weight: {stats['current_weight_lbs']} lbs | "
            f"Height: {stats.get('current_height_ft')} ft"
        )

    diet = stats.get("diet", {})
    if diet.get("avg_calories_7d") is not None:
        lines.append(
            f"- Diet (7-day avg): {diet['avg_calories_7d']} kcal/day | "
            f"TDEE: ~{diet.get('estimated_tdee', '?')} kcal | "
            f"Surplus/Deficit: {diet.get('calorie_deficit_surplus_vs_tdee', '?')} kcal"
        )
    if diet.get("avg_protein_g_7d") is not None:
        lines.append(
            f"  Macros: Protein {diet['avg_protein_g_7d']}g | "
            f"Carbs {diet.get('avg_carbs_g_7d', '?')}g | "
            f"Fat {diet.get('avg_fat_g_7d', '?')}g"
        )

    sleep = stats.get("sleep", {})
    if sleep.get("avg_duration_hrs_7d") is not None:
        lines.append(
            f"- Sleep (7-day avg): {sleep['avg_duration_hrs_7d']} hrs | "
            f"Consistency score: {sleep.get('sleep_consistency_score', '?')}/100 | "
            f"Average quality: {sleep.get('avg_quality_7d', '?')}/5"
        )

    exercise = stats.get("exercise", {})
    if exercise.get("avg_daily_met_30d") is not None:
        lines.append(
            f"- Exercise (30-day avg MET): {exercise['avg_daily_met_30d']} | "
            f"Cardio sessions/week: {exercise.get('cardio_sessions_per_week', '?')} | "
            f"Activity trend: {exercise.get('activity_trend', 'unknown')}"
        )

    period = stats.get("period", {})
    if period.get("cycle_phase") and period["cycle_phase"] != "unknown":
        lines.append(
            f"- Menstrual cycle phase: {period['cycle_phase']}"
            + (
                f" | Flow: {period['current_flow_amount']}"
                if period.get("current_flow_amount")
                else ""
            )
        )

    return "\n".join(lines) if lines else "No recent health data available."


def _format_clinical(entries: Sequence[ClinicalHistoryEntry]) -> str:
    if not entries:
        return "No clinical history on file."

    lines: list[str] = []
    for entry in entries[:5]:
        parts = [entry.illness_name]
        if entry.diagnosis_date:
            parts.append(f"diagnosed {entry.diagnosis_date.isoformat()}")
        if entry.start_date or entry.end_date:
            parts.append(
                "active window: "
                f"{entry.start_date.isoformat() if entry.start_date else '?'}"
                f" to {entry.end_date.isoformat() if entry.end_date else 'present'}"
            )
        if entry.medication:
            parts.append(f"medication: {entry.medication}")
        lines.append("- " + " | ".join(parts))
    return "\n".join(lines)


def _format_apple_health_export(ah: dict) -> str:
    """Format the richer Apple Health export data for AI context."""
    from datetime import date, timedelta

    totals = ah.get("totals", {})
    daily_steps = ah.get("daily_steps", {})
    daily_workouts = ah.get("daily_workouts", {})
    daily_sleep = ah.get("daily_sleep", {})
    daily_energy = ah.get("daily_active_energy", {})

    lines = [
        f"- Data source: Apple Health export (parsed {ah.get('synced_at', 'unknown')[:10]})",
        f"- Steps (30d): {totals.get('total_steps_30d', 0):,} total | {totals.get('avg_daily_steps', 0):,} avg/day",
        f"- Steps (7d): {totals.get('total_steps_7d', 0):,} total | {totals.get('avg_daily_steps_7d', 0):,} avg/day",
    ]

    # Recent 7 days steps
    today = date.today()
    step_lines = []
    for i in range(6, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        step_lines.append(f"{d[5:]}: {daily_steps.get(d, 0):,}")
    lines.append(f"- Daily steps (last 7d): {', '.join(step_lines)}")

    # Workouts
    workout_count = totals.get("total_workout_sessions_30d", 0)
    workout_types = totals.get("workout_type_counts", {})
    avg_min = totals.get("avg_workout_min_per_session", 0)
    type_str = ", ".join(f"{k}: {v}" for k, v in list(workout_types.items())[:5])
    lines.append(f"- Workouts (30d): {workout_count} sessions | {avg_min} min avg/session")
    if type_str:
        lines.append(f"- Workout types: {type_str}")
    lines.append(f"- Exercise (7d): {totals.get('avg_workout_min_7d', 0)} avg min/day")

    # Active energy
    if daily_energy:
        recent_energy = sum(
            v for d, v in daily_energy.items() if d >= (today - timedelta(days=6)).isoformat()
        )
        lines.append(f"- Active energy burned (7d): {round(recent_energy):,} kcal total")

    # Sleep
    if daily_sleep:
        recent_sleep = [
            v for d, v in daily_sleep.items() if d >= (today - timedelta(days=6)).isoformat()
        ]
        if recent_sleep:
            avg_sleep = round(sum(recent_sleep) / len(recent_sleep), 2)
            lines.append(f"- Sleep (7d): {avg_sleep} hrs/night avg ({len(recent_sleep)} nights tracked)")
        else:
            lines.append("- Sleep: no recent data in Apple Health export")
    else:
        lines.append("- Sleep: no sleep data in Apple Health export")

    return "\n".join(lines)


def _format_apple_health(ah: dict | None) -> str:
    if not ah:
        return "No Apple Health data synced yet."

    source = ah.get("source", "mock")
    if source == "export":
        return _format_apple_health_export(ah)

    # Legacy mock format (7-element arrays)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    steps_str = ", ".join(
        f"{days[i]}: {s:,}" for i, s in enumerate(ah.get("steps", []))
    )
    sleep_str = ", ".join(
        f"{days[i]}: {h}h" for i, h in enumerate(ah.get("sleep", []))
    )
    lines = [
        f"- Last synced: {ah.get('synced_at', 'unknown')}",
        f"- Steps (7d): {steps_str}",
        f"- Total steps: {ah.get('total_steps_7d', 0):,} | Avg/day: {ah.get('avg_daily_steps', 0):,}",
        f"- Sleep (7d): {sleep_str}",
        f"- Avg sleep: {ah.get('avg_sleep_hrs', 0)} hrs/night",
    ]
    if ah.get("midweek_sleep_drop"):
        lines.append("- Pattern: midweek sleep drop detected (Wed–Fri below average)")
    if ah.get("high_activity_fluctuation"):
        lines.append("- Pattern: high step-count fluctuation across the week")
    return "\n".join(lines)


def build_chat_system_prompt(
    user: UserProfile,
    stats: dict,
    clinical_entries: Sequence[ClinicalHistoryEntry],
    apple_health: dict | None = None,
) -> str:
    return _SYSTEM_TEMPLATE.format(
        name=user.name,
        age=user.age,
        sex="Male" if user.sex == "M" else "Female",
        stats_summary=_format_stats(stats),
        apple_health_summary=_format_apple_health(apple_health),
        clinical_summary=_format_clinical(clinical_entries),
    )


_DASHBOARD_ANALYSIS_SYSTEM_TEMPLATE = """\
You are generating short dashboard summaries for a health tracking app.
Use only the provided statistics.
Do not mention missing data as an error.
If data is limited, briefly say there is not enough recent history.
Do not diagnose disease or provide urgent medical advice
unless the stats clearly suggest professional follow-up.
Return strict JSON only. No markdown, no code fences, no extra commentary.
"""


def build_dashboard_analysis_user_prompt(
    user: UserProfile,
    stats: dict[str, Any],
) -> str:
    payload = {
        "user_profile": {
            "name": user.name,
            "age": user.age,
            "sex": user.sex,
        },
        "dashboard_stats": stats,
        "required_response_shape": {
            "basic": {
                "7d": "short summary string",
                "30d": "short summary string",
            },
            "diet": {
                "7d": "short summary string",
                "30d": "short summary string",
            },
            "exercise": {
                "7d": "short summary string",
                "30d": "short summary string",
            },
            "sleep": {
                "7d": "short summary string",
                "30d": "short summary string",
            },
            "overall_summary": "2-4 sentence overall dashboard summary",
        },
        "writing_rules": [
            "Each summary should be concise and readable in a dashboard card.",
            "Mention trends or comparisons when useful.",
            "If data is sparse, say there is limited recent data.",
            "Avoid markdown or bullet points.",
        ],
    }
    return json.dumps(payload, indent=2, default=str)
