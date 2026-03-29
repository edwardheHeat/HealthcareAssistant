"""Manual monitor trigger router.

POST /api/v1/monitor/trigger runs the monitor for the current user
against all metrics using the latest stored data + pre-computed stats.
Useful for testing, admin tooling, and future dashboard "Run Check" button.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.alerts import Alert
from app.models.health_records import (
    BasicIndicatorRecord,
    DietRecord,
    ExerciseRecord,
    PeriodRecord,
    SleepRecord,
)
from app.schemas.alerts import AlertRead
from app.services.monitor import trigger_monitor
from app.services.monitor_types import (
    BasicIndicatorSnapshot,
    DietSnapshot,
    ExerciseSnapshot,
    PeriodSnapshot,
    SleepSnapshot,
)
from app.services.stats import build_user_stats_context

router = APIRouter(prefix="/monitor", tags=["monitor"])

_DEFAULT_USER_ID = 1


@router.post("/trigger", response_model=list[AlertRead])
async def manual_trigger(db: Session = Depends(get_db)) -> list[Alert]:
    """Run monitor checks across all metrics using the latest stored records.

    Builds a typed snapshot per metric from the most recent record + current
    trend stats, then calls trigger_monitor for each. Returns all newly
    generated alerts (empty list if everything looks healthy).
    """
    user_id = _DEFAULT_USER_ID
    trend_stats = build_user_stats_context(db, user_id)
    new_alerts: list[Alert] = []

    # ---- Basic Indicators --------------------------------------------------
    latest_bi = db.scalars(
        select(BasicIndicatorRecord)
        .where(BasicIndicatorRecord.user_id == user_id)
        .order_by(BasicIndicatorRecord.recorded_at.desc())
        .limit(2)
    ).all()

    if latest_bi:
        current = latest_bi[0]
        prev_weight = latest_bi[1].weight_lbs if len(latest_bi) > 1 else None
        cm = current.height_ft * 30.48
        kg = current.weight_lbs * 0.453592
        prev_kg = prev_weight * 0.453592 if prev_weight else None

        snap = BasicIndicatorSnapshot(
            current_height_cm=cm,
            current_weight_kg=kg,
            previous_weight_kg=prev_kg,
            trend_stats=trend_stats,
        )
        alert = await trigger_monitor(db, user_id, snap)
        if alert:
            new_alerts.append(alert)

    # ---- Diet --------------------------------------------------------------
    latest_diet = db.scalars(
        select(DietRecord)
        .where(DietRecord.user_id == user_id)
        .order_by(DietRecord.recorded_at.desc())
        .limit(1)
    ).first()

    if latest_diet:
        snap = DietSnapshot(
            current_calories=latest_diet.calorie_intake,
            trend_stats=trend_stats,
        )
        alert = await trigger_monitor(db, user_id, snap)
        if alert:
            new_alerts.append(alert)

    # ---- Sleep -------------------------------------------------------------
    latest_sleep = db.scalars(
        select(SleepRecord)
        .where(SleepRecord.user_id == user_id)
        .order_by(SleepRecord.sleep_start.desc())
        .limit(2)
    ).all()

    if latest_sleep:
        current = latest_sleep[0]
        dur = (current.wake_time - current.sleep_start).total_seconds() / 3600
        prev_dur = None
        if len(latest_sleep) > 1:
            p = latest_sleep[1]
            prev_dur = (p.wake_time - p.sleep_start).total_seconds() / 3600
        snap = SleepSnapshot(
            current_duration_hrs=dur,
            current_quality=3, # Mock default
            previous_duration_hrs=prev_dur,
            trend_stats=trend_stats,
        )
        alert = await trigger_monitor(db, user_id, snap)
        if alert:
            new_alerts.append(alert)

    # ---- Exercise ----------------------------------------------------------
    latest_ex = db.scalars(
        select(ExerciseRecord)
        .where(ExerciseRecord.user_id == user_id)
        .order_by(ExerciseRecord.recorded_at.desc())
        .limit(1)
    ).first()

    if latest_ex:
        snap = ExerciseSnapshot(
            exercise_days_7d=1,
            exercise_days_30d_avg_per_week=1.0,
            trend_stats=trend_stats,
        )
        alert = await trigger_monitor(db, user_id, snap)
        if alert:
            new_alerts.append(alert)

    # ---- Period ------------------------------------------------------------
    latest_period = db.scalars(
        select(PeriodRecord)
        .where(PeriodRecord.user_id == user_id)
        .order_by(PeriodRecord.recorded_at.desc())
        .limit(1)
    ).first()

    if latest_period:
        from datetime import date
        snap = PeriodSnapshot(
            start_date=date.today(), # Mock default
            end_date=None,
            trend_stats=trend_stats,
        )
        alert = await trigger_monitor(db, user_id, snap)
        if alert:
            new_alerts.append(alert)

    return new_alerts
