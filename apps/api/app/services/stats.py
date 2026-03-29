"""Statistical context builder for dashboard and LLM prompts."""

import statistics
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.daily_tracking import (
    DailyBasicMetrics,
    DailyDiet,
    DailyExercise,
    DailySleep,
)
from app.models.health_records import PeriodRecord
from app.models.user import UserProfile

_NOW = lambda: datetime.now(tz=UTC)  # noqa: E731

_EXERCISE_MET = {
    "low": 3.0,
    "medium": 6.0,
    "high": 9.0,
}


def _days_ago(n: int) -> date:
    return (_NOW() - timedelta(days=n)).date()


def _kg_to_lbs(weight_kg: float) -> float:
    return round(weight_kg / 0.45359237, 1)


def _cm_to_ft(height_cm: float) -> float:
    return round(height_cm / 30.48, 2)


def _bmi(weight_kg: float, height_cm: float) -> float:
    height_m = height_cm / 100.0
    if height_m == 0:
        return 0.0
    return round(weight_kg / (height_m**2), 1)


def _exercise_met(duration_minutes: int, intensity: str) -> float:
    intensity_met = _EXERCISE_MET[intensity]
    exercise_hours = duration_minutes / 60.0
    rest_hours = max(0.0, 16.0 - exercise_hours)
    return round((intensity_met * exercise_hours + 1.5 * rest_hours) / 16.0, 2)


def _tdee(
    user: UserProfile,
    avg_met: float,
    current_weight_kg: float | None,
    current_height_cm: float | None,
) -> float:
    weight_kg = current_weight_kg or (70.0 if user.sex == "M" else 60.0)
    height_cm = current_height_cm or (170.0 if user.sex == "M" else 160.0)
    if user.sex == "M":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * user.age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * user.age - 161
    pal = max(1.2, min(2.5, avg_met))
    return round(bmr * pal, 0)


def _trend(values: list[float]) -> str:
    if len(values) < 3:
        return "stable"
    delta = values[-1] - values[0]
    if abs(delta) < 1.0:
        return "stable"
    return "gaining" if delta > 0 else "losing"


def _sleep_consistency_score(
    sleep_times: list[datetime],
    wake_times: list[datetime],
) -> int:
    if not sleep_times:
        return 0
    sleep_hours = [t.hour + t.minute / 60 for t in sleep_times]
    wake_hours = [t.hour + t.minute / 60 for t in wake_times]
    std = (
        statistics.stdev(sleep_hours) + statistics.stdev(wake_hours)
        if len(sleep_hours) > 1
        else 0
    )
    return max(0, int(100 - (std / 6.0) * 100))


def _cycle_phase(last_flow_date: datetime | None, has_flow_today: bool) -> str:
    if has_flow_today:
        return "menstrual"
    if last_flow_date is None:
        return "unknown"
    days_since = (_NOW() - last_flow_date).days
    if days_since <= 5:
        return "menstrual"
    if days_since <= 13:
        return "follicular"
    if days_since <= 16:
        return "ovulatory"
    return "luteal"


def build_user_stats_context(db: Session, user_id: int) -> dict:
    user = db.get(UserProfile, user_id)
    if user is None:
        return {}

    stats: dict = {"user_id": user_id}

    basic_30 = db.scalars(
        select(DailyBasicMetrics)
        .where(
            DailyBasicMetrics.user_id == user_id,
            DailyBasicMetrics.date >= _days_ago(30),
        )
        .order_by(DailyBasicMetrics.date)
    ).all()

    current_weight_kg: float | None = None
    current_height_cm: float | None = None
    if basic_30:
        current = basic_30[-1]
        current_weight_kg = current.weight_kg
        current_height_cm = current.height_cm
        stats["current_weight_kg"] = current.weight_kg
        stats["current_height_cm"] = current.height_cm
        stats["current_weight_lbs"] = _kg_to_lbs(current.weight_kg)
        stats["current_height_ft"] = _cm_to_ft(current.height_cm)
        stats["bmi"] = _bmi(current.weight_kg, current.height_cm)
        stats["weight_trend"] = _trend([r.weight_kg for r in basic_30])
        stats["height_trend"] = _trend([r.height_cm for r in basic_30])
        stats["last_bi_recorded_at"] = current.date.isoformat()
    else:
        stats["current_weight_kg"] = None
        stats["current_height_cm"] = None
        stats["current_weight_lbs"] = None
        stats["current_height_ft"] = None
        stats["bmi"] = None
        stats["weight_trend"] = "unknown"
        stats["height_trend"] = "unknown"
        stats["last_bi_recorded_at"] = None

    diet_7 = db.scalars(
        select(DailyDiet).where(
            DailyDiet.user_id == user_id,
            DailyDiet.date >= _days_ago(7),
        )
    ).all()

    calories = [
        r.breakfast_calories + r.lunch_calories + r.dinner_calories for r in diet_7
    ]
    proteins = [r.protein_g for r in diet_7]
    carbs = [r.carbs_g for r in diet_7]
    fats = [r.fat_g for r in diet_7]

    avg_calories = statistics.mean(calories) if calories else None
    calorie_variance = statistics.variance(calories) if len(calories) > 1 else None

    exercise_30 = db.scalars(
        select(DailyExercise)
        .where(
            DailyExercise.user_id == user_id,
            DailyExercise.date >= _days_ago(30),
        )
        .order_by(DailyExercise.date)
    ).all()
    met_values = [_exercise_met(r.duration_minutes, r.intensity) for r in exercise_30]
    avg_met = statistics.mean(met_values) if met_values else 1.5
    tdee = _tdee(user, avg_met, current_weight_kg, current_height_cm)

    stats["diet"] = {
        "avg_calories_7d": round(avg_calories, 1) if avg_calories is not None else None,
        "calorie_variance_7d": (
            round(calorie_variance, 1) if calorie_variance is not None else None
        ),
        "calorie_deficit_surplus_vs_tdee": (
            round(avg_calories - tdee, 1) if avg_calories is not None else None
        ),
        "estimated_tdee": tdee,
        "avg_protein_g_7d": round(statistics.mean(proteins), 1) if proteins else None,
        "avg_carbs_g_7d": round(statistics.mean(carbs), 1) if carbs else None,
        "avg_fat_g_7d": round(statistics.mean(fats), 1) if fats else None,
        "last_recorded_at": max((r.date for r in diet_7), default=None),
    }
    if stats["diet"]["last_recorded_at"] is not None:
        stats["diet"]["last_recorded_at"] = stats["diet"][
            "last_recorded_at"
        ].isoformat()

    sleep_7 = db.scalars(
        select(DailySleep).where(
            DailySleep.user_id == user_id,
            DailySleep.date >= _days_ago(7),
        )
    ).all()
    durations = [
        (r.sleep_end - r.sleep_start).total_seconds() / 3600 for r in sleep_7
    ]
    avg_sleep = statistics.mean(durations) if durations else None
    recommended_min, recommended_max = 7.0, 9.0
    deviation = (
        min(abs(avg_sleep - recommended_min), abs(avg_sleep - recommended_max))
        if avg_sleep is not None
        else None
    )

    stats["sleep"] = {
        "avg_duration_hrs_7d": round(avg_sleep, 2) if avg_sleep is not None else None,
        "sleep_consistency_score": (
            _sleep_consistency_score(
                [r.sleep_start for r in sleep_7],
                [r.sleep_end for r in sleep_7],
            )
            if sleep_7
            else None
        ),
        "deviation_from_recommended_hrs": (
            round(deviation, 2) if deviation is not None else None
        ),
        "avg_quality_7d": (
            round(statistics.mean([r.quality for r in sleep_7]), 1) if sleep_7 else None
        ),
        "last_recorded_at": max((r.date for r in sleep_7), default=None),
    }
    if stats["sleep"]["last_recorded_at"] is not None:
        stats["sleep"]["last_recorded_at"] = stats["sleep"][
            "last_recorded_at"
        ].isoformat()

    exercise_7 = [r for r in exercise_30 if r.date >= _days_ago(7)]
    cardio_sessions = sum(1 for r in exercise_7 if r.duration_minutes >= 20)
    avg_exercise_met = round(statistics.mean(met_values), 2) if met_values else None

    stats["exercise"] = {
        "avg_daily_met_30d": avg_exercise_met,
        "cardio_sessions_per_week": cardio_sessions,
        "activity_trend": _trend(met_values) if len(met_values) >= 3 else "stable",
        "last_recorded_at": max((r.date for r in exercise_30), default=None),
    }
    if stats["exercise"]["last_recorded_at"] is not None:
        stats["exercise"]["last_recorded_at"] = stats["exercise"][
            "last_recorded_at"
        ].isoformat()

    period_recent = db.scalars(
        select(PeriodRecord)
        .where(PeriodRecord.user_id == user_id)
        .order_by(PeriodRecord.recorded_at.desc())
        .limit(30)
    ).all()
    has_flow_today = bool(
        period_recent
        and period_recent[0].has_flow
        and (_NOW() - period_recent[0].recorded_at).days == 0
    )
    last_flow = next((r.recorded_at for r in period_recent if r.has_flow), None)
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
