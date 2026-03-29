"""Health records router."""

from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
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


from app.schemas.alerts import AlertRead
from app.services.met import compute_met
from app.services.monitor import trigger_monitor
from app.services.monitor_types import (
    BasicIndicatorSnapshot,
    DietSnapshot,
    ExerciseSnapshot,
    PeriodSnapshot,
    SleepSnapshot,
)
from app.services.stats import build_user_stats_context

from app.services.analysis import analyze_after_submission


router = APIRouter(prefix="/health", tags=["health"])

_DEFAULT_USER_ID = 1


def _get_user_or_404(db: Session) -> UserProfile:
    user = db.get(UserProfile, _DEFAULT_USER_ID)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found. Create one first.")
    return user


def _upsert_daily_record(
    db: Session,
    model: type[DailyBasicMetrics | DailyDiet | DailyExercise | DailySleep],
    record_date: Any,
    values: dict[str, Any],
) -> DailyBasicMetrics | DailyDiet | DailyExercise | DailySleep:
    record = db.scalars(
        select(model).where(
            model.user_id == _DEFAULT_USER_ID,
            model.date == record_date,
        )
    ).first()

    if record is None:
        record = model(user_id=_DEFAULT_USER_ID, date=record_date, **values)
        db.add(record)
    else:
        for field, value in values.items():
            setattr(record, field, value)
    return record


@router.post("/basic-indicators", response_model=BasicIndicatorRead, status_code=201)
async def submit_basic_indicators(
    payload: BasicIndicatorCreate,
    db: Session = Depends(get_db),
) -> DailyBasicMetrics:
    _get_user_or_404(db)
<<<<<<< HEAD
    
    prev_bi = db.scalars(select(BasicIndicatorRecord).where(BasicIndicatorRecord.user_id == _DEFAULT_USER_ID).order_by(BasicIndicatorRecord.recorded_at.desc()).limit(1)).first()
    
    record = BasicIndicatorRecord(user_id=_DEFAULT_USER_ID, **payload.model_dump())
    db.add(record)
=======
    record = _upsert_daily_record(
        db,
        DailyBasicMetrics,
        payload.date,
        {
            "height_cm": payload.height_cm,
            "weight_kg": payload.weight_kg,
        },
    )
>>>>>>> c3e846b (WIP Kiana: db+stat+analysis ver. 1)
    db.commit()
    db.refresh(record)
    
    trend_stats = build_user_stats_context(db, _DEFAULT_USER_ID)
    cm = record.height_ft * 30.48
    prev_cm = prev_bi.height_ft * 30.48 if prev_bi else None
    kg = record.weight_lbs * 0.453592
    prev_kg = prev_bi.weight_lbs * 0.453592 if prev_bi else None

    snap = BasicIndicatorSnapshot(
        current_height_cm=cm,
        previous_height_cm=prev_cm,
        current_weight_kg=kg,
        previous_weight_kg=prev_kg,
        trend_stats=trend_stats,
    )
    await trigger_monitor(db, _DEFAULT_USER_ID, snap)
    return record


@router.get("/basic-indicators", response_model=list[BasicIndicatorRead])
def list_basic_indicators(
    limit: int = 30,
    db: Session = Depends(get_db),
) -> list[DailyBasicMetrics]:
    return db.scalars(
        select(DailyBasicMetrics)
        .where(DailyBasicMetrics.user_id == _DEFAULT_USER_ID)
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
    db: Session = Depends(get_db),
) -> DailyDiet:
    _get_user_or_404(db)
    payload = DietRecordCreate(
        user_id=_DEFAULT_USER_ID,
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

    trend_stats = build_user_stats_context(db, _DEFAULT_USER_ID)
    snap = DietSnapshot(
        current_calories=record.calorie_intake,
        trend_stats=trend_stats,
    )
    await trigger_monitor(db, _DEFAULT_USER_ID, snap)
    return record


@router.get("/diet", response_model=list[DietRecordRead])
def list_diet(limit: int = 30, db: Session = Depends(get_db)) -> list[DailyDiet]:
    return db.scalars(
        select(DailyDiet)
        .where(DailyDiet.user_id == _DEFAULT_USER_ID)
        .order_by(DailyDiet.date.desc())
        .limit(limit)
    ).all()


@router.post("/sleep", response_model=SleepRecordRead, status_code=201)
def submit_sleep(
    payload: SleepRecordCreate,
    db: Session = Depends(get_db),
) -> DailySleep:
    _get_user_or_404(db)
    record = _upsert_daily_record(
        db,
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
    analyze_after_submission(db, _DEFAULT_USER_ID)
    return record


@router.get("/sleep", response_model=list[SleepRecordRead])
def list_sleep(limit: int = 30, db: Session = Depends(get_db)) -> list[DailySleep]:
    return db.scalars(
        select(DailySleep)
        .where(DailySleep.user_id == _DEFAULT_USER_ID)
        .order_by(DailySleep.date.desc())
        .limit(limit)
    ).all()


@router.post("/exercise", response_model=ExerciseRecordRead, status_code=201)
async def submit_exercise(
    payload: ExerciseRecordCreate,
    db: Session = Depends(get_db),
) -> DailyExercise:
    _get_user_or_404(db)
<<<<<<< HEAD
    user = db.get(UserProfile, _DEFAULT_USER_ID)
    # Actually, we shouldn't calculate this if user is None, but _get_user_or_404 ensures it
    met_value = compute_met(
        activity_level=payload.work_activity_level,
        intensity=payload.exercise_intensity,
        duration_min=payload.duration_min,
        age_years=user.age,
        sex=user.sex,
    )
    record = ExerciseRecord(
        user_id=_DEFAULT_USER_ID, met_value=met_value, **payload.model_dump()
    )
    db.add(record)
=======
    record = _upsert_daily_record(
        db,
        DailyExercise,
        payload.date,
        {
            "duration_minutes": payload.duration_minutes,
            "intensity": payload.intensity,
        },
    )
>>>>>>> c3e846b (WIP Kiana: db+stat+analysis ver. 1)
    db.commit()
    db.refresh(record)

    trend_stats = build_user_stats_context(db, _DEFAULT_USER_ID)
    snap = ExerciseSnapshot(
        exercise_days_7d=1, # Mock default
        exercise_days_30d_avg_per_week=1.0, 
        trend_stats=trend_stats
    )
    await trigger_monitor(db, _DEFAULT_USER_ID, snap)
    return record


@router.get("/exercise", response_model=list[ExerciseRecordRead])
def list_exercise(
    limit: int = 30,
    db: Session = Depends(get_db),
) -> list[DailyExercise]:
    return db.scalars(
        select(DailyExercise)
        .where(DailyExercise.user_id == _DEFAULT_USER_ID)
        .order_by(DailyExercise.date.desc())
        .limit(limit)
    ).all()


@router.post("/period", response_model=PeriodRecordRead, status_code=201)
async def submit_period(
    payload: PeriodRecordCreate,
    db: Session = Depends(get_db),
) -> PeriodRecord:
    _get_user_or_404(db)
    record = PeriodRecord(user_id=_DEFAULT_USER_ID, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)

    from datetime import date
    trend_stats = build_user_stats_context(db, _DEFAULT_USER_ID)
    snap = PeriodSnapshot(
        start_date=date.today(), # Mock default
        end_date=None,
        trend_stats=trend_stats,
    )
    await trigger_monitor(db, _DEFAULT_USER_ID, snap)
    return record


@router.get("/period", response_model=list[PeriodRecordRead])
def list_period(limit: int = 30, db: Session = Depends(get_db)) -> list[PeriodRecord]:
    return db.scalars(
        select(PeriodRecord)
        .where(PeriodRecord.user_id == _DEFAULT_USER_ID)
        .order_by(PeriodRecord.recorded_at.desc())
        .limit(limit)
    ).all()
