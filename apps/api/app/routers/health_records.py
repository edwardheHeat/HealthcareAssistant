"""Health records router."""

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models.daily_tracking import (
    DailyBasicMetrics,
    DailyDiet,
    DailyExercise,
    DailySleep,
)
from app.models.health_records import PeriodRecord
from app.models.user import UserProfile
from app.schemas.health_records import (
    BasicIndicatorCreate,
    BasicIndicatorRead,
    DietRecordCreate,
    DietRecordRead,
    ExerciseRecordCreate,
    ExerciseRecordRead,
    PeriodRecordCreate,
    PeriodRecordRead,
    SleepRecordCreate,
    SleepRecordRead,
)
from app.services.analysis import analyze_after_submission
from app.services.analysis_generation import refresh_dashboard_analysis
from app.services.monitor import trigger_monitor
from app.services.monitor_types import (
    BasicIndicatorSnapshot,
    DietSnapshot,
    ExerciseSnapshot,
    PeriodSnapshot,
)
from app.services.stats import build_user_stats_context

router = APIRouter(prefix="/health", tags=["health"])


def _upsert_daily_record(
    db: Session,
    user_id: int,
    model: type[DailyBasicMetrics | DailyDiet | DailyExercise | DailySleep],
    record_date: Any,
    values: dict[str, Any],
) -> DailyBasicMetrics | DailyDiet | DailyExercise | DailySleep:
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


def _get_previous_basic_metrics(
    db: Session,
    user_id: int,
    record_date: Any,
) -> DailyBasicMetrics | None:
    return db.scalars(
        select(DailyBasicMetrics)
        .where(
            DailyBasicMetrics.user_id == user_id,
            DailyBasicMetrics.date < record_date,
        )
        .order_by(DailyBasicMetrics.date.desc())
        .limit(1)
    ).first()


def _build_exercise_snapshot(
    db: Session,
    user_id: int,
    record: DailyExercise,
    trend_stats: dict[str, Any],
) -> ExerciseSnapshot:
    records_7d = db.scalars(
        select(DailyExercise.date).where(
            DailyExercise.user_id == user_id,
            DailyExercise.date >= record.date - timedelta(days=6),
            DailyExercise.date <= record.date,
        )
    ).all()
    records_30d = db.scalars(
        select(DailyExercise.date).where(
            DailyExercise.user_id == user_id,
            DailyExercise.date >= record.date - timedelta(days=29),
            DailyExercise.date <= record.date,
        )
    ).all()
    return ExerciseSnapshot(
        exercise_days_7d=len(records_7d),
        exercise_days_30d_avg_per_week=round((len(records_30d) * 7) / 30, 2),
        trend_stats=trend_stats,
    )


@router.post("/basic-indicators", response_model=BasicIndicatorRead, status_code=201)
async def submit_basic_indicators(
    payload: BasicIndicatorCreate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailyBasicMetrics:
    record = _upsert_daily_record(
        db,
        current_user.id,
        DailyBasicMetrics,
        payload.date,
        {
            "height_cm": payload.height_cm,
            "weight_kg": payload.weight_kg,
        },
    )
    db.commit()
    db.refresh(record)

    previous = _get_previous_basic_metrics(db, current_user.id, record.date)
    trend_stats = build_user_stats_context(db, current_user.id)

    snap = BasicIndicatorSnapshot(
        current_height_cm=record.height_cm,
        previous_height_cm=previous.height_cm if previous else None,
        current_weight_kg=record.weight_kg,
        previous_weight_kg=previous.weight_kg if previous else None,
        trend_stats=trend_stats,
    )
    await trigger_monitor(db, current_user.id, snap)
    refresh_dashboard_analysis(db, current_user.id)
    return record


@router.get("/basic-indicators", response_model=list[BasicIndicatorRead])
def list_basic_indicators(
    limit: int = 30,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DailyBasicMetrics]:
    return db.scalars(
        select(DailyBasicMetrics)
        .where(DailyBasicMetrics.user_id == current_user.id)
        .order_by(DailyBasicMetrics.date.desc())
        .limit(limit)
    ).all()


@router.post("/diet", response_model=DietRecordRead, status_code=201)
async def submit_diet(
    breakfast_calories: int | None = Form(None),
    lunch_calories: int | None = Form(None),
    dinner_calories: int | None = Form(None),
    calorie_intake: int | None = Form(None),
    protein_g: float = Form(0),
    carbs_g: float = Form(0),
    fat_g: float = Form(0),
    food_image: UploadFile | None = File(None),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailyDiet:
    payload = DietRecordCreate(
        user_id=current_user.id,
        breakfast_calories=breakfast_calories,
        lunch_calories=lunch_calories,
        dinner_calories=dinner_calories,
        calorie_intake=calorie_intake,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
    )

    # The current normalized schema does not persist images, but we still accept
    # the field to avoid breaking existing clients during the transition.
    _ = food_image

    record = _upsert_daily_record(
        db,
        current_user.id,
        DailyDiet,
        payload.date,
        {
            "breakfast_calories": payload.breakfast_calories,
            "lunch_calories": payload.lunch_calories,
            "dinner_calories": payload.dinner_calories,
            "protein_g": payload.protein_g,
            "carbs_g": payload.carbs_g,
            "fat_g": payload.fat_g,
        },
    )
    db.commit()
    db.refresh(record)

    trend_stats = build_user_stats_context(db, current_user.id)
    snap = DietSnapshot(
        current_calories=(
            record.breakfast_calories + record.lunch_calories + record.dinner_calories
        ),
        trend_stats=trend_stats,
    )
    await trigger_monitor(db, current_user.id, snap)
    refresh_dashboard_analysis(db, current_user.id)
    return record


@router.get("/diet", response_model=list[DietRecordRead])
def list_diet(
    limit: int = 30,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DailyDiet]:
    return db.scalars(
        select(DailyDiet)
        .where(DailyDiet.user_id == current_user.id)
        .order_by(DailyDiet.date.desc())
        .limit(limit)
    ).all()


@router.post("/sleep", response_model=SleepRecordRead, status_code=201)
def submit_sleep(
    payload: SleepRecordCreate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailySleep:
    record = _upsert_daily_record(
        db,
        current_user.id,
        DailySleep,
        payload.date,
        {
            "sleep_start": payload.sleep_start,
            "sleep_end": payload.sleep_end,
            "quality": payload.quality,
        },
    )
    db.commit()
    db.refresh(record)
    analyze_after_submission(db, current_user.id)
    return record


@router.get("/sleep", response_model=list[SleepRecordRead])
def list_sleep(
    limit: int = 30,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DailySleep]:
    return db.scalars(
        select(DailySleep)
        .where(DailySleep.user_id == current_user.id)
        .order_by(DailySleep.date.desc())
        .limit(limit)
    ).all()


@router.post("/exercise", response_model=ExerciseRecordRead, status_code=201)
async def submit_exercise(
    payload: ExerciseRecordCreate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailyExercise:
    record = _upsert_daily_record(
        db,
        current_user.id,
        DailyExercise,
        payload.date,
        {
            "duration_minutes": payload.duration_minutes,
            "intensity": payload.intensity,
        },
    )
    db.commit()
    db.refresh(record)

    trend_stats = build_user_stats_context(db, current_user.id)
    snap = _build_exercise_snapshot(db, current_user.id, record, trend_stats)
    await trigger_monitor(db, current_user.id, snap)
    refresh_dashboard_analysis(db, current_user.id)
    return record


@router.get("/exercise", response_model=list[ExerciseRecordRead])
def list_exercise(
    limit: int = 30,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DailyExercise]:
    return db.scalars(
        select(DailyExercise)
        .where(DailyExercise.user_id == current_user.id)
        .order_by(DailyExercise.date.desc())
        .limit(limit)
    ).all()


@router.post("/period", response_model=PeriodRecordRead, status_code=201)
async def submit_period(
    payload: PeriodRecordCreate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PeriodRecord:
    record = PeriodRecord(user_id=current_user.id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)

    from datetime import date

    trend_stats = build_user_stats_context(db, current_user.id)
    snap = PeriodSnapshot(
        start_date=date.today(),  # Mock default
        end_date=None,
        trend_stats=trend_stats,
    )
    await trigger_monitor(db, current_user.id, snap)
    refresh_dashboard_analysis(db, current_user.id)
    return record


@router.get("/period", response_model=list[PeriodRecordRead])
def list_period(
    limit: int = 30,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PeriodRecord]:
    return db.scalars(
        select(PeriodRecord)
        .where(PeriodRecord.user_id == current_user.id)
        .order_by(PeriodRecord.recorded_at.desc())
        .limit(limit)
    ).all()
