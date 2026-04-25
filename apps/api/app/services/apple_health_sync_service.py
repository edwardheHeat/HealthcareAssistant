"""Service for synchronizing Apple Health data into core tracking records."""

import logging
from datetime import date, datetime, timedelta, time, UTC
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.daily_tracking import DailyExercise, DailySleep
from app.models.apple_health import AppleHealthExport
from app.services.monitor import trigger_monitor
from app.services.analysis_generation import refresh_dashboard_analysis
from app.services.stats import build_user_stats_context
from app.services.monitor_types import ExerciseSnapshot

logger = logging.getLogger(__name__)

def _upsert_daily_record(
    db: Session,
    user_id: int,
    model: type[DailyExercise | DailySleep],
    record_date: date,
    values: dict,
) -> DailyExercise | DailySleep:
    record = db.scalars(
        select(model).where(
            model.user_id == user_id,
            model.date == record_date,
        )
    ).first()

    if record is None:
        record = model(user_id=user_id, date=record_date, **values)
        db.add(record)
    else:
        for field, value in values.items():
            setattr(record, field, value)
    return record

async def sync_ah_to_core(db: Session, user_id: int):
    """
    Finds the latest AppleHealthExport for a user and syncs its daily data
    into the DailySleep and DailyExercise tables.
    """
    export = db.scalars(
        select(AppleHealthExport)
        .where(AppleHealthExport.user_id == user_id)
        .order_by(AppleHealthExport.parsed_at.desc())
        .limit(1)
    ).first()

    if not export:
        logger.info("No AppleHealthExport found for user %s, skipping core sync", user_id)
        return

    daily_steps = export.daily_steps
    daily_sleep = export.daily_sleep
    daily_workouts = export.daily_workouts

    # Sync Sleep
    for date_str, duration_hrs in daily_sleep.items():
        record_date = date.fromisoformat(date_str)
        
        # Apple Health usually gives us duration. We'll simulate start/end
        # if they aren't provided in the export.
        # In this project's DailySleep model, we need sleep_start and sleep_end (datetime).
        # We'll assume a standard 11 PM to [Duration] AM window for mock-up sync.
        start_dt = datetime.combine(record_date - timedelta(days=1), time(23, 0)).replace(tzinfo=UTC)
        end_dt = start_dt + timedelta(hours=duration_hrs)
        
        _upsert_daily_record(
            db, user_id, DailySleep, record_date,
            {
                "sleep_start": start_dt,
                "sleep_end": end_dt,
                "quality": 3  # Default 'Good' for wearable data unless specified
            }
        )

    # Sync Exercise (Workouts)
    for date_str, workouts in daily_workouts.items():
        record_date = date.fromisoformat(date_str)
        total_min = sum(float(w.get("duration_min", 0)) for w in workouts)
        
        if total_min > 0:
            # Pick highest intensity workout as the daily intensity
            intensities = [w.get("type", "medium") for w in workouts]
            # Simple mapping for demo
            final_intensity = "medium"
            if any(i in ["Running", "HIIT"] for i in intensities):
                final_intensity = "high"
            
            _upsert_daily_record(
                db, user_id, DailyExercise, record_date,
                {
                    "duration_minutes": total_min,
                    "intensity": final_intensity
                }
            )

    db.commit()
    
    # After syncing records, we trigger the monitor for the most recent day to ensure dashboard alerts update
    latest_date = max([date.fromisoformat(d) for d in daily_sleep.keys()] + [date.today()], default=date.today())
    
    # Refresh dashboard AI
    refresh_dashboard_analysis(db, user_id)
    
    logger.info("Successfully synced Apple Health data to core records for user %s", user_id)

def _build_exercise_snapshot(
    db: Session,
    user_id: int,
    record_date: date,
    trend_stats: dict,
) -> ExerciseSnapshot:
    records_7d = db.scalars(
        select(DailyExercise.date).where(
            DailyExercise.user_id == user_id,
            DailyExercise.date >= record_date - timedelta(days=6),
            DailyExercise.date <= record_date,
        )
    ).all()
    records_30d = db.scalars(
        select(DailyExercise.date).where(
            DailyExercise.user_id == user_id,
            DailyExercise.date >= record_date - timedelta(days=29),
            DailyExercise.date <= record_date,
        )
    ).all()
    return ExerciseSnapshot(
        exercise_days_7d=len(records_7d),
        exercise_days_30d_avg_per_week=round((len(records_30d) * 7) / 30, 2),
        trend_stats=trend_stats,
    )
