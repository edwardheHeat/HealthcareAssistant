"""LLM prompt templates and context builder.

All prompt text lives here — never inline in service or router files.
"""

from app.models.clinical import ClinicalHistory
from app.models.user import UserProfile

# ---------------------------------------------------------------------------
# System prompt template
# ---------------------------------------------------------------------------

_SYSTEM_TEMPLATE = """\
You are a compassionate and knowledgeable personal health assistant.
You have access to the user's health profile and recent statistics (provided below).
Your role is to:
- Answer health-related questions using the user's personal data as context.
- Help narrow down causes of symptoms (provide at most 3 possibilities).
- Recommend when to seek professional medical care.
- Respect any hard constraints in the user's clinical history (e.g. injury restrictions).

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
## Clinical History
{clinical_summary}
---
"""


def _format_stats(stats: dict) -> str:
    """Convert the stats dict into a readable bullet-point summary."""
    lines: list[str] = []

    # Basic indicators
    if stats.get("bmi"):
        lines.append(f"- BMI: {stats['bmi']} (weight trend: {stats.get('weight_trend', 'unknown')})")
    if stats.get("current_weight_lbs"):
        lines.append(f"- Weight: {stats['current_weight_lbs']} lbs | Height: {stats.get('current_height_ft')} ft")

    # Diet
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

    # Sleep
    sleep = stats.get("sleep", {})
    if sleep.get("avg_duration_hrs_7d") is not None:
        lines.append(
            f"- Sleep (7-day avg): {sleep['avg_duration_hrs_7d']} hrs | "
            f"Consistency score: {sleep.get('sleep_consistency_score', '?')}/100 | "
            f"Deviation from 7–9 h: {sleep.get('deviation_from_recommended_hrs', '?')} hrs"
        )

    # Exercise
    ex = stats.get("exercise", {})
    if ex.get("avg_daily_met_30d") is not None:
        lines.append(
            f"- Exercise (30-day avg MET): {ex['avg_daily_met_30d']} | "
            f"Cardio sessions/week: {ex.get('cardio_sessions_per_week', '?')} | "
            f"Activity trend: {ex.get('activity_trend', 'unknown')}"
        )

    # Period
    period = stats.get("period", {})
    if period.get("cycle_phase") and period["cycle_phase"] != "unknown":
        lines.append(
            f"- Menstrual cycle phase: {period['cycle_phase']}"
            + (f" | Flow: {period['current_flow_amount']}" if period.get("current_flow_amount") else "")
        )

    return "\n".join(lines) if lines else "No recent health data available."


def _format_clinical(clinical: ClinicalHistory | None) -> str:
    if clinical is None:
        return "No clinical history on file."
    parts: list[str] = []
    if clinical.injuries:
        parts.append(f"Injuries: {clinical.injuries}")
    if clinical.surgeries:
        parts.append(f"Surgeries: {clinical.surgeries}")
    if clinical.constraints:
        parts.append(f"Hard constraints: {clinical.constraints}")
    return "\n".join(parts) if parts else "No significant clinical history."


def build_chat_system_prompt(
    user: UserProfile,
    stats: dict,
    clinical: ClinicalHistory | None,
) -> str:
    """Build the full system prompt for a chat session."""
    return _SYSTEM_TEMPLATE.format(
        name=user.name,
        age=user.age,
        sex="Male" if user.sex == "M" else "Female",
        stats_summary=_format_stats(stats),
        clinical_summary=_format_clinical(clinical),
    )
