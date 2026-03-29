"""Statistical context builder for LLM prompts and dashboard display.

build_user_stats_context() queries recent DB records and returns a dict of
computed statistics. This dict is used both for:
  1. Frontend dashboard display
  2. LLM system prompt context (via llm/prompts.py)
"""

import math
import statistics
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.health_records import (
    BasicIndicatorRecord,
    DietRecord,
    ExerciseRecord,
    FlowAmount,
    PeriodRecord,
    SleepRecord,
)
from app.models.user import UserProfile

_NOW = lambda: datetime.now(tz=timezone.utc)  # noqa: E731


def _days_ago(n: int) -> datetime:
    return _NOW() - timedelta(days=n)


# --------------------------------------------------------------------------- #
# BMI helpers                                                                  #
# --------------------------------------------------------------------------- #

def _bmi(weight_lbs: float, height_ft: float) -> float:
    height_m = height_ft * 0.3048
    weight_kg = weight_lbs * 0.453592
    if height_m == 0:
        return 0.0
    return round(weight_kg / (height_m**2), 1)


# --------------------------------------------------------------------------- #
# TDEE estimate (Mifflin-St Jeor + PAL)                                       #
# --------------------------------------------------------------------------- #

def _tdee(user: UserProfile, avg_met: float) -> float:
    """Rough TDEE estimate in kcal/day using Mifflin-St Jeor BMR × PAL."""
    # We don't store exact height/weight on the profile, so we use recent record.
    # Caller is responsible for passing valid user object.
    # PAL ≈ avg_met / 1.0 (since MET is already a ratio to rest)
    # Simplified: BMR varies, use age + sex only heuristic
    if user.sex == "M":
        bmr = 10 * 70 + 6.25 * 170 - 5 * user.age + 5  # placeholder body
    else:
        bmr = 10 * 60 + 6.25 * 160 - 5 * user.age - 161
    pal = max(1.2, min(2.5, avg_met))
    return round(bmr * pal, 0)


# --------------------------------------------------------------------------- #
# Trend helper                                                                 #
# --------------------------------------------------------------------------- #

def _trend(values: list[float]) -> str:
    """Return 'gaining', 'losing', or 'stable' from a time-ordered sequence."""
    if len(values) < 3:
        return "stable"
    delta = values[-1] - values[0]
    if abs(delta) < 1.0:
        return "stable"
    return "gaining" if delta > 0 else "losing"


# --------------------------------------------------------------------------- #
# Sleep consistency score (0–100)                                              #
# --------------------------------------------------------------------------- #

def _sleep_consistency_score(sleep_times: list[datetime], wake_times: list[datetime]) -> int:
    """Higher = more regular schedule. Based on std-dev of sleep/wake hour-of-day."""
    if not sleep_times:
        return 0
    sleep_hours = [t.hour + t.minute / 60 for t in sleep_times]
    wake_hours = [t.hour + t.minute / 60 for t in wake_times]
    std = (
        statistics.stdev(sleep_hours) + statistics.stdev(wake_hours)
        if len(sleep_hours) > 1
        else 0
    )
    # std of 0 → score 100; std of 6 → score 0
    score = max(0, int(100 - (std / 6.0) * 100))
    return score


# --------------------------------------------------------------------------- #
# Menstrual cycle phase                                                         #
# --------------------------------------------------------------------------- #

def _cycle_phase(last_flow_date: datetime | None, has_flow_today: bool) -> str:
    """Estimate current cycle phase from last known flow anchor."""
    if has_flow_today:
        return "menstrual"
    if last_flow_date is None:
        return "unknown"
    days_since = (_NOW() - last_flow_date).days
    if days_since <= 5:
        return "menstrual"
    elif days_since <= 13:
        return "follicular"
    elif days_since <= 16:
        return "ovulatory"
    else:
        return "luteal"


# --------------------------------------------------------------------------- #
# Main builder                                                                  #
# --------------------------------------------------------------------------- #

def build_user_stats_context(db: Session, user_id: int) -> dict:
    """Build a comprehensive stats dict for dashboard + LLM context."""

    user = db.get(UserProfile, user_id)
    if user is None:
        return {}

    stats: dict = {"user_id": user_id}

    # ---- Basic Indicators ------------------------------------------------- #
    bi_30 = db.scalars(
        select(BasicIndicatorRecord)
        .where(
            BasicIndicatorRecord.user_id == user_id,
            BasicIndicatorRecord.recorded_at >= _days_ago(30),
        )
        .order_by(BasicIndicatorRecord.recorded_at)
    ).all()

    if bi_30:
        current = bi_30[-1]
        stats["current_weight_lbs"] = current.weight_lbs
        stats["current_height_ft"] = current.height_ft
        stats["bmi"] = _bmi(current.weight_lbs, current.height_ft)
        stats["weight_trend"] = _trend([r.weight_lbs for r in bi_30])
        stats["height_trend"] = _trend([r.height_ft for r in bi_30])
        stats["last_bi_recorded_at"] = current.recorded_at.isoformat()
    else:
        stats["current_weight_lbs"] = None
        stats["current_height_ft"] = None
        stats["bmi"] = None
        stats["weight_trend"] = "unknown"
        stats["height_trend"] = "unknown"
        stats["last_bi_recorded_at"] = None

    # ---- Diet ------------------------------------------------------------- #
    diet_7 = db.scalars(
        select(DietRecord)
        .where(
            DietRecord.user_id == user_id,
            DietRecord.recorded_at >= _days_ago(7),
        )
    ).all()

    calories = [r.calorie_intake for r in diet_7]
    proteins = [r.protein_g for r in diet_7 if r.protein_g is not None]
    carbs = [r.carbs_g for r in diet_7 if r.carbs_g is not None]
    fats = [r.fat_g for r in diet_7 if r.fat_g is not None]

    avg_calories = statistics.mean(calories) if calories else None
    calorie_variance = statistics.variance(calories) if len(calories) > 1 else None

    # Rough TDEE for deficit/surplus
    avg_met_guess = stats.get("avg_daily_met") or 1.5
    tdee = _tdee(user, avg_met_guess)
    calorie_deficit_surplus = (
        round(avg_calories - tdee, 1) if avg_calories is not None else None
    )

    stats["diet"] = {
        "avg_calories_7d": round(avg_calories, 1) if avg_calories else None,
        "calorie_variance_7d": round(calorie_variance, 1) if calorie_variance else None,
        "calorie_deficit_surplus_vs_tdee": calorie_deficit_surplus,
        "estimated_tdee": tdee,
        "avg_protein_g_7d": round(statistics.mean(proteins), 1) if proteins else None,
        "avg_carbs_g_7d": round(statistics.mean(carbs), 1) if carbs else None,
        "avg_fat_g_7d": round(statistics.mean(fats), 1) if fats else None,
        "last_recorded_at": (
            max(r.recorded_at for r in diet_7).isoformat() if diet_7 else None
        ),
    }

    # ---- Sleep ------------------------------------------------------------ #
    sleep_7 = db.scalars(
        select(SleepRecord)
        .where(
            SleepRecord.user_id == user_id,
            SleepRecord.sleep_start >= _days_ago(7),
        )
    ).all()

    durations = [
        (r.wake_time - r.sleep_start).total_seconds() / 3600 for r in sleep_7
    ]
    avg_sleep = statistics.mean(durations) if durations else None
    recommended_min, recommended_max = 7.0, 9.0
    deviation = (
        min(abs(avg_sleep - recommended_min), abs(avg_sleep - recommended_max))
        if avg_sleep is not None
        else None
    )

    stats["sleep"] = {
        "avg_duration_hrs_7d": round(avg_sleep, 2) if avg_sleep else None,
        "sleep_consistency_score": (
            _sleep_consistency_score(
                [r.sleep_start for r in sleep_7],
                [r.wake_time for r in sleep_7],
            )
            if sleep_7
            else None
        ),
        "deviation_from_recommended_hrs": round(deviation, 2) if deviation else None,
        "last_recorded_at": (
            max(r.sleep_start for r in sleep_7).isoformat() if sleep_7 else None
        ),
    }

    # ---- Exercise --------------------------------------------------------- #
    ex_30 = db.scalars(
        select(ExerciseRecord)
        .where(
            ExerciseRecord.user_id == user_id,
            ExerciseRecord.recorded_at >= _days_ago(30),
        )
        .order_by(ExerciseRecord.recorded_at)
    ).all()

    met_values = [r.met_value for r in ex_30]
    avg_met = statistics.mean(met_values) if met_values else None

    # Weekly cardio sessions heuristic: any activity not "weightlifting"
    ex_7 = [r for r in ex_30 if r.recorded_at >= _days_ago(7)]
    cardio_sessions = sum(
        1
        for r in ex_7
        if "weight" not in r.exercise_type.lower()
        and "lift" not in r.exercise_type.lower()
    )

    stats["exercise"] = {
        "avg_daily_met_30d": round(avg_met, 2) if avg_met else None,
        "cardio_sessions_per_week": cardio_sessions,
        "activity_trend": _trend(met_values) if len(met_values) >= 3 else "stable",
        "last_recorded_at": (
            max(r.recorded_at for r in ex_30).isoformat() if ex_30 else None
        ),
    }

    # Now we have avg_met, re-compute TDEE for diet deficit/surplus
    if avg_met:
        tdee = _tdee(user, avg_met)
        stats["diet"]["estimated_tdee"] = tdee
        if avg_calories is not None:
            stats["diet"]["calorie_deficit_surplus_vs_tdee"] = round(
                avg_calories - tdee, 1
            )

    # ---- Period ----------------------------------------------------------- #
    period_recent = db.scalars(
        select(PeriodRecord)
        .where(
            PeriodRecord.user_id == user_id,
        )
        .order_by(PeriodRecord.recorded_at.desc())
        .limit(30)
    ).all()

    has_flow_today = bool(
        period_recent and period_recent[0].has_flow
        and (_NOW() - period_recent[0].recorded_at).days == 0
    )
    last_flow = next(
        (r.recorded_at for r in period_recent if r.has_flow), None
    )
    current_flow_amount = (
        period_recent[0].flow_amount.value
        if period_recent and period_recent[0].has_flow and period_recent[0].flow_amount
        else None
    )

    stats["period"] = {
        "cycle_phase": _cycle_phase(last_flow, has_flow_today),
        "current_flow_amount": current_flow_amount,
        "last_recorded_at": (
            period_recent[0].recorded_at.isoformat() if period_recent else None
        ),
    }

    return stats
