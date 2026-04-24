"""Dashboard analysis helpers.

All derived statistics are computed on demand in the service layer.
Nothing here persists averages back into the database.
"""

from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from typing import Any, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis import IndicatorAnalysis, OverallAnalysis
from app.models.apple_health import AppleHealthExport, AppleHealthSync
from app.models.daily_tracking import (
    DailyBasicMetrics,
    DailyDiet,
    DailyExercise,
    DailySleep,
)
from app.models.reproductive import PeriodCycle

T = TypeVar("T")

_TODAY = lambda: datetime.now(tz=UTC).date()  # noqa: E731
_ANALYSIS_CATEGORIES = ("basic", "diet", "exercise", "sleep")
_ANALYSIS_PERIODS = ("7d", "30d")


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def _window_start(days: int, *, anchor_date: date | None = None) -> date:
    end_date = anchor_date or _TODAY()
    return end_date - timedelta(days=days - 1)


def _previous_window_bounds(
    days: int,
    *,
    anchor_date: date | None = None,
) -> tuple[date, date]:
    end_date = anchor_date or _TODAY()
    previous_end = end_date - timedelta(days=days)
    previous_start = previous_end - timedelta(days=days - 1)
    return previous_start, previous_end


def _filter_logs_by_date(
    logs: list[T],
    *,
    start_date: date,
    end_date: date | None = None,
) -> list[T]:
    effective_end = end_date or _TODAY()
    return [log for log in logs if start_date <= getattr(log, "date") <= effective_end]


def _build_bar_chart(
    logs: list[T],
    *,
    days: int,
    value_getter: Callable[[T], float | int | None],
    anchor_date: date | None = None,
) -> list[dict[str, Any]]:
    end_date = anchor_date or _TODAY()
    start_date = end_date - timedelta(days=days - 1)
    value_by_date = {
        getattr(log, "date"): value_getter(log)
        for log in logs
        if start_date <= getattr(log, "date") <= end_date
    }

    chart: list[dict[str, Any]] = []
    current = start_date
    while current <= end_date:
        chart.append(
            {
                "date": current.isoformat(),
                "value": value_by_date.get(current),
            }
        )
        current += timedelta(days=1)
    return chart


def _sleep_duration_hours(log: DailySleep) -> float:
    duration = log.sleep_end - log.sleep_start
    return round(duration.total_seconds() / 3600, 2)


def _diet_total_calories(log: DailyDiet) -> int:
    return log.breakfast_calories + log.lunch_calories + log.dinner_calories


def compute_basic_stats(logs: list[DailyBasicMetrics]) -> dict[str, Any]:
    sorted_logs = sorted(logs, key=lambda log: log.date)
    logs_7d = _filter_logs_by_date(logs, start_date=_window_start(7))
    logs_30d = _filter_logs_by_date(logs, start_date=_window_start(30))
    prev_start, prev_end = _previous_window_bounds(30)
    previous_logs_30d = _filter_logs_by_date(
        logs,
        start_date=prev_start,
        end_date=prev_end,
    )

    avg_weight_7d = _mean([log.weight_kg for log in logs_7d])
    avg_weight_30d = _mean([log.weight_kg for log in logs_30d])
    previous_avg_weight_30d = _mean([log.weight_kg for log in previous_logs_30d])

    return {
        "avg_weight_7d": avg_weight_7d,
        "avg_weight_30d": avg_weight_30d,
        "previous_avg_weight_30d": previous_avg_weight_30d,
        "weight_trend": (
            round(avg_weight_30d - previous_avg_weight_30d, 2)
            if avg_weight_30d is not None and previous_avg_weight_30d is not None
            else None
        ),
        "latest_weight_kg": sorted_logs[-1].weight_kg if sorted_logs else None,
        "bar_chart_data": {
            "last_7_days": _build_bar_chart(
                logs,
                days=7,
                value_getter=lambda log: log.weight_kg,
            ),
            "last_30_days": _build_bar_chart(
                logs,
                days=30,
                value_getter=lambda log: log.weight_kg,
            ),
        },
    }


def compute_diet_stats(logs: list[DailyDiet]) -> dict[str, Any]:
    logs_7d = _filter_logs_by_date(logs, start_date=_window_start(7))
    logs_30d = _filter_logs_by_date(logs, start_date=_window_start(30))
    prev_start, prev_end = _previous_window_bounds(30)
    previous_logs_30d = _filter_logs_by_date(
        logs,
        start_date=prev_start,
        end_date=prev_end,
    )

    avg_calories_7d = _mean([_diet_total_calories(log) for log in logs_7d])
    avg_calories_30d = _mean([_diet_total_calories(log) for log in logs_30d])
    previous_avg_calories_30d = _mean(
        [_diet_total_calories(log) for log in previous_logs_30d]
    )

    return {
        "avg_calories_7d": avg_calories_7d,
        "avg_calories_30d": avg_calories_30d,
        "previous_avg_calories_30d": previous_avg_calories_30d,
        "calories_trend": (
            round(avg_calories_30d - previous_avg_calories_30d, 2)
            if avg_calories_30d is not None and previous_avg_calories_30d is not None
            else None
        ),
        "avg_protein_g_7d": _mean([log.protein_g for log in logs_7d]),
        "avg_protein_g_30d": _mean([log.protein_g for log in logs_30d]),
        "avg_carbs_g_7d": _mean([log.carbs_g for log in logs_7d]),
        "avg_carbs_g_30d": _mean([log.carbs_g for log in logs_30d]),
        "avg_fat_g_7d": _mean([log.fat_g for log in logs_7d]),
        "avg_fat_g_30d": _mean([log.fat_g for log in logs_30d]),
        "bar_chart_data": {
            "last_7_days": _build_bar_chart(
                logs,
                days=7,
                value_getter=_diet_total_calories,
            ),
            "last_30_days": _build_bar_chart(
                logs,
                days=30,
                value_getter=_diet_total_calories,
            ),
        },
    }


def compute_exercise_stats(logs: list[DailyExercise]) -> dict[str, Any]:
    logs_7d = _filter_logs_by_date(logs, start_date=_window_start(7))
    logs_30d = _filter_logs_by_date(logs, start_date=_window_start(30))
    prev_start, prev_end = _previous_window_bounds(30)
    previous_logs_30d = _filter_logs_by_date(
        logs,
        start_date=prev_start,
        end_date=prev_end,
    )

    avg_duration_7d = _mean([float(log.duration_minutes) for log in logs_7d])
    avg_duration_30d = _mean([float(log.duration_minutes) for log in logs_30d])
    previous_avg_duration_30d = _mean(
        [float(log.duration_minutes) for log in previous_logs_30d]
    )

    intensity_distribution = {
        "low": sum(1 for log in logs_30d if log.intensity == "low"),
        "medium": sum(1 for log in logs_30d if log.intensity == "medium"),
        "high": sum(1 for log in logs_30d if log.intensity == "high"),
    }

    return {
        "avg_duration_7d": avg_duration_7d,
        "avg_duration_30d": avg_duration_30d,
        "previous_avg_duration_30d": previous_avg_duration_30d,
        "duration_trend": (
            round(avg_duration_30d - previous_avg_duration_30d, 2)
            if avg_duration_30d is not None and previous_avg_duration_30d is not None
            else None
        ),
        "intensity_distribution": intensity_distribution,
        "bar_chart_data": {
            "last_7_days": _build_bar_chart(
                logs,
                days=7,
                value_getter=lambda log: log.duration_minutes,
            ),
            "last_30_days": _build_bar_chart(
                logs,
                days=30,
                value_getter=lambda log: log.duration_minutes,
            ),
        },
    }


def compute_sleep_stats(logs: list[DailySleep]) -> dict[str, Any]:
    logs_7d = _filter_logs_by_date(logs, start_date=_window_start(7))
    logs_30d = _filter_logs_by_date(logs, start_date=_window_start(30))
    prev_start, prev_end = _previous_window_bounds(30)
    previous_logs_30d = _filter_logs_by_date(
        logs,
        start_date=prev_start,
        end_date=prev_end,
    )

    avg_sleep_duration_7d = _mean([_sleep_duration_hours(log) for log in logs_7d])
    avg_sleep_duration_30d = _mean([_sleep_duration_hours(log) for log in logs_30d])
    previous_avg_sleep_duration_30d = _mean(
        [_sleep_duration_hours(log) for log in previous_logs_30d]
    )

    return {
        "avg_sleep_duration_7d": avg_sleep_duration_7d,
        "avg_sleep_duration_30d": avg_sleep_duration_30d,
        "previous_avg_sleep_duration_30d": previous_avg_sleep_duration_30d,
        "sleep_trend": (
            round(avg_sleep_duration_30d - previous_avg_sleep_duration_30d, 2)
            if (
                avg_sleep_duration_30d is not None
                and previous_avg_sleep_duration_30d is not None
            )
            else None
        ),
        "avg_quality_7d": _mean([float(log.quality) for log in logs_7d]),
        "avg_quality_30d": _mean([float(log.quality) for log in logs_30d]),
        "bar_chart_data": {
            "last_7_days": _build_bar_chart(
                logs,
                days=7,
                value_getter=_sleep_duration_hours,
            ),
            "last_30_days": _build_bar_chart(
                logs,
                days=30,
                value_getter=_sleep_duration_hours,
            ),
        },
    }


def _compute_period_cycle_from_logs(logs: list[PeriodCycle]) -> dict[str, Any]:
    if not logs:
        return {
            "last_cycle_start": None,
            "last_cycle_end": None,
            "avg_cycle_length_days": None,
            "predicted_next_start_start": None,
            "predicted_next_start_end": None,
        }

    sorted_logs = sorted(logs, key=lambda log: log.start_date)
    last_cycle = sorted_logs[-1]

    cycle_lengths = [
        (current.start_date - previous.start_date).days
        for previous, current in zip(sorted_logs, sorted_logs[1:])
    ]
    if not cycle_lengths:
        cycle_lengths = [(last_cycle.end_date - last_cycle.start_date).days]

    avg_cycle_length_days = _mean([float(days) for days in cycle_lengths])
    if avg_cycle_length_days is None:
        return {
            "last_cycle_start": last_cycle.start_date.isoformat(),
            "last_cycle_end": last_cycle.end_date.isoformat(),
            "avg_cycle_length_days": None,
            "predicted_next_start_start": None,
            "predicted_next_start_end": None,
        }

    predicted_next_start = last_cycle.start_date + timedelta(
        days=round(avg_cycle_length_days)
    )
    return {
        "last_cycle_start": last_cycle.start_date.isoformat(),
        "last_cycle_end": last_cycle.end_date.isoformat(),
        "avg_cycle_length_days": avg_cycle_length_days,
        "predicted_next_start_start": (
            predicted_next_start - timedelta(days=2)
        ).isoformat(),
        "predicted_next_start_end": (
            predicted_next_start + timedelta(days=2)
        ).isoformat(),
    }


def compute_period_cycle(user_id: int, db: Session) -> dict[str, Any]:
    start_date = _TODAY() - timedelta(days=365)
    cycles = db.scalars(
        select(PeriodCycle)
        .where(
            PeriodCycle.user_id == user_id,
            PeriodCycle.start_date >= start_date,
        )
        .order_by(PeriodCycle.start_date.asc())
    ).all()
    return _compute_period_cycle_from_logs(cycles)


def _ah_to_chart_points(values: list[float | int]) -> list[dict[str, Any]]:
    """Convert a 7-element Apple Health array to last-7-days chart points."""
    today = _TODAY()
    return [
        {"date": (today - timedelta(days=6 - i)).isoformat(), "value": v}
        for i, v in enumerate(values)
    ]


def _daily_dict_to_chart_points(
    values_by_date: dict[str, float | int],
    *,
    days: int,
) -> list[dict[str, Any]]:
    today = _TODAY()
    return [
        {
            "date": (today - timedelta(days=days - 1 - i)).isoformat(),
            "value": values_by_date.get(
                (today - timedelta(days=days - 1 - i)).isoformat()
            ),
        }
        for i in range(days)
    ]


def _steps_and_energy_from_export(export: AppleHealthExport) -> dict[str, Any]:
    totals = export.totals
    daily_steps = export.daily_steps
    daily_active_energy = export.daily_active_energy
    today = _TODAY()
    start_7d = (today - timedelta(days=6)).isoformat()

    return {
        "avg_daily_steps": totals.get("avg_daily_steps"),
        "avg_daily_steps_7d": totals.get("avg_daily_steps_7d"),
        "total_steps_7d": totals.get("total_steps_7d"),
        "total_steps_30d": totals.get("total_steps_30d"),
        "steps_bar_chart_7d": _daily_dict_to_chart_points(daily_steps, days=7),
        "steps_bar_chart_30d": _daily_dict_to_chart_points(daily_steps, days=30),
        "active_energy_7d": round(
            sum(v for k, v in daily_active_energy.items() if k >= start_7d),
            1,
        ),
    }


def _workout_intensity(workout_type: str) -> str:
    if workout_type in {
        "Running",
        "HIIT",
        "CrossTraining",
        "JumpRope",
        "StepTraining",
        "Cycling",
        "Swimming",
    }:
        return "high"
    if workout_type in {"Walking", "Stairs"}:
        return "low"
    return "medium"


def _exercise_stats_from_export(export: AppleHealthExport) -> dict[str, Any]:
    daily_workouts = export.daily_workouts
    totals = export.totals
    duration_by_date = {
        day: round(
            sum(float(workout.get("duration_min", 0)) for workout in workouts), 1
        )
        for day, workouts in daily_workouts.items()
    }
    intensity_distribution = {"low": 0, "medium": 0, "high": 0}
    for workouts in daily_workouts.values():
        for workout in workouts:
            intensity = _workout_intensity(str(workout.get("type", "")))
            intensity_distribution[intensity] += 1

    return {
        "avg_duration_7d": totals.get("avg_workout_min_7d"),
        "avg_duration_30d": totals.get("avg_workout_min_30d"),
        "intensity_distribution": intensity_distribution,
        "bar_chart_data": {
            "last_7_days": _daily_dict_to_chart_points(duration_by_date, days=7),
            "last_30_days": _daily_dict_to_chart_points(duration_by_date, days=30),
        },
    }


def compute_dashboard_stat_blocks(user_id: int, db: Session) -> dict[str, Any]:
    daily_start_date = _TODAY() - timedelta(days=59)

    basic_logs = db.scalars(
        select(DailyBasicMetrics)
        .where(
            DailyBasicMetrics.user_id == user_id,
            DailyBasicMetrics.date >= daily_start_date,
        )
        .order_by(DailyBasicMetrics.date.asc())
    ).all()
    diet_logs = db.scalars(
        select(DailyDiet)
        .where(
            DailyDiet.user_id == user_id,
            DailyDiet.date >= daily_start_date,
        )
        .order_by(DailyDiet.date.asc())
    ).all()
    exercise_logs = db.scalars(
        select(DailyExercise)
        .where(
            DailyExercise.user_id == user_id,
            DailyExercise.date >= daily_start_date,
        )
        .order_by(DailyExercise.date.asc())
    ).all()
    sleep_logs = db.scalars(
        select(DailySleep)
        .where(
            DailySleep.user_id == user_id,
            DailySleep.date >= daily_start_date,
        )
        .order_by(DailySleep.date.asc())
    ).all()

    sleep_stats = compute_sleep_stats(sleep_logs)
    exercise_stats = compute_exercise_stats(exercise_logs)

    # Check for AppleHealthExport first (new, richer format with 30-day data)
    ah_export = db.scalars(
        select(AppleHealthExport)
        .where(AppleHealthExport.user_id == user_id)
        .order_by(AppleHealthExport.parsed_at.desc())
        .limit(1)
    ).first()

    if ah_export is not None:
        # Always merge steps and energy data
        steps_data = _steps_and_energy_from_export(ah_export)
        exercise_stats.update(steps_data)

        # Merge exercise duration from workouts when no manual data exists
        if exercise_stats["avg_duration_7d"] is None:
            workout_stats = _exercise_stats_from_export(ah_export)
            exercise_stats["avg_duration_7d"] = workout_stats["avg_duration_7d"]
            exercise_stats["avg_duration_30d"] = workout_stats["avg_duration_30d"]
            exercise_stats["intensity_distribution"] = workout_stats[
                "intensity_distribution"
            ]
            exercise_stats["bar_chart_data"] = workout_stats["bar_chart_data"]

        # Merge sleep from export when no manual data exists
        if sleep_stats["avg_sleep_duration_7d"] is None:
            ah_sleep = ah_export.daily_sleep
            if ah_sleep:
                today = _TODAY()
                start_7d = (today - timedelta(days=6)).isoformat()
                sleep_7d = [v for k, v in ah_sleep.items() if k >= start_7d]
                if sleep_7d:
                    sleep_stats["avg_sleep_duration_7d"] = round(
                        sum(sleep_7d) / len(sleep_7d), 2
                    )
                    sleep_stats["bar_chart_data"]["last_7_days"] = [
                        {
                            "date": (today - timedelta(days=6 - i)).isoformat(),
                            "value": ah_sleep.get(
                                (today - timedelta(days=6 - i)).isoformat()
                            ),
                        }
                        for i in range(7)
                    ]
    else:
        # Fallback: old-style AppleHealthSync (mock 7-element arrays)
        ah = db.scalars(
            select(AppleHealthSync)
            .where(AppleHealthSync.user_id == user_id)
            .order_by(AppleHealthSync.synced_at.desc())
            .limit(1)
        ).first()

        if ah is not None:
            ah_sleep = ah.sleep
            ah_steps = ah.steps

            # Fill sleep stats with AH data when no manual logs exist
            if sleep_stats["avg_sleep_duration_7d"] is None and ah_sleep:
                sleep_stats["avg_sleep_duration_7d"] = round(
                    sum(ah_sleep) / len(ah_sleep), 2
                )
                sleep_stats["bar_chart_data"]["last_7_days"] = _ah_to_chart_points(
                    ah_sleep
                )

            # Inject steps into exercise stats
            if ah_steps:
                exercise_stats["avg_daily_steps"] = round(sum(ah_steps) / len(ah_steps))
                exercise_stats["total_steps_7d"] = sum(ah_steps)
                exercise_stats["steps_bar_chart_7d"] = _ah_to_chart_points(ah_steps)

    return {
        "basic": compute_basic_stats(basic_logs),
        "diet": compute_diet_stats(diet_logs),
        "exercise": exercise_stats,
        "sleep": sleep_stats,
        "period_cycle": compute_period_cycle(user_id, db),
    }


def get_latest_indicator_analysis(
    user_id: int, db: Session
) -> dict[str, dict[str, str | None]]:
    analysis: dict[str, dict[str, str | None]] = {}

    for category in _ANALYSIS_CATEGORIES:
        analysis[category] = {}
        for period_type in _ANALYSIS_PERIODS:
            latest_record = db.scalars(
                select(IndicatorAnalysis)
                .where(
                    IndicatorAnalysis.user_id == user_id,
                    IndicatorAnalysis.category == category,
                    IndicatorAnalysis.period_type == period_type,
                )
                .order_by(IndicatorAnalysis.created_at.desc())
                .limit(1)
            ).first()
            analysis[category][period_type] = (
                latest_record.analysis_text if latest_record is not None else None
            )

    return analysis


def get_latest_overall_analysis(user_id: int, db: Session) -> dict[str, Any] | None:
    latest_record = db.scalars(
        select(OverallAnalysis)
        .where(OverallAnalysis.user_id == user_id)
        .order_by(OverallAnalysis.created_at.desc())
        .limit(1)
    ).first()

    if latest_record is None:
        return None

    return {
        "summary": latest_record.summary_text,
        "created_at": latest_record.created_at.isoformat(),
    }


def get_apple_health_summary(user_id: int, db: Session) -> dict[str, Any] | None:
    # Prefer the richer export format
    export = db.scalars(
        select(AppleHealthExport)
        .where(AppleHealthExport.user_id == user_id)
        .order_by(AppleHealthExport.parsed_at.desc())
        .limit(1)
    ).first()

    if export is not None:
        totals = export.totals
        return {
            "source": "export",
            "synced_at": export.parsed_at.isoformat(),
            "totals": totals,
            "daily_steps": export.daily_steps,
            "daily_workouts": export.daily_workouts,
            "daily_sleep": export.daily_sleep,
            "daily_active_energy": export.daily_active_energy,
        }

    # Fallback to old sync format
    record = db.scalars(
        select(AppleHealthSync)
        .where(AppleHealthSync.user_id == user_id)
        .order_by(AppleHealthSync.synced_at.desc())
        .limit(1)
    ).first()
    if record is None:
        return None
    steps = record.steps
    sleep = record.sleep
    avg_sleep = round(sum(sleep) / len(sleep), 2) if sleep else 0.0
    midweek_avg = (
        round(sum(sleep[i] for i in [2, 3, 4]) / 3, 2) if len(sleep) >= 5 else avg_sleep
    )
    return {
        "source": "mock",
        "synced_at": record.synced_at.isoformat(),
        "steps": steps,
        "sleep": sleep,
        "total_steps_7d": sum(steps),
        "avg_daily_steps": round(sum(steps) / len(steps)) if steps else 0,
        "avg_sleep_hrs": avg_sleep,
        "midweek_sleep_drop": (avg_sleep - midweek_avg) > 0.5,
        "high_activity_fluctuation": (max(steps) - min(steps)) > 4000
        if steps
        else False,
    }


def get_dashboard_stats(user_id: int, db: Session) -> dict[str, Any]:
    return {
        "stats": compute_dashboard_stat_blocks(user_id, db),
        "analysis": get_latest_indicator_analysis(user_id, db),
        "overall_analysis": get_latest_overall_analysis(user_id, db),
        "apple_health": get_apple_health_summary(user_id, db),
    }
