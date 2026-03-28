"""Health records router — accepts all health metric submissions."""

import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.health_records import (
    BasicIndicatorRecord,
    DietRecord,
    ExerciseIntensity,
    ExerciseRecord,
    FlowAmount,
    PeriodRecord,
    SleepRecord,
    WorkActivityLevel,
)
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
from app.services.analysis import analyze_after_submission
from app.services.met import compute_met

router = APIRouter(prefix="/health", tags=["health"])

_DEFAULT_USER_ID = 1


def _get_user_or_404(db: Session) -> UserProfile:
    user = db.get(UserProfile, _DEFAULT_USER_ID)
    if user is None:
        raise HTTPException(status_code=404, detail="User profile not found. Create one first.")
    return user


# --------------------------------------------------------------------------- #
# Basic Indicators                                                             #
# --------------------------------------------------------------------------- #

@router.post("/basic-indicators", response_model=BasicIndicatorRead, status_code=201)
def submit_basic_indicators(
    payload: BasicIndicatorCreate,
    db: Session = Depends(get_db),
) -> BasicIndicatorRecord:
    _get_user_or_404(db)
    record = BasicIndicatorRecord(user_id=_DEFAULT_USER_ID, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    analyze_after_submission(db, _DEFAULT_USER_ID)
    return record


@router.get("/basic-indicators", response_model=list[BasicIndicatorRead])
def list_basic_indicators(
    limit: int = 30,
    db: Session = Depends(get_db),
) -> list[BasicIndicatorRecord]:
    return db.scalars(  # type: ignore[return-value]
        select(BasicIndicatorRecord)
        .where(BasicIndicatorRecord.user_id == _DEFAULT_USER_ID)
        .order_by(BasicIndicatorRecord.recorded_at.desc())
        .limit(limit)
    ).all()


# --------------------------------------------------------------------------- #
# Diet                                                                         #
# --------------------------------------------------------------------------- #

@router.post("/diet", response_model=DietRecordRead, status_code=201)
async def submit_diet(
    calorie_intake: float = Form(...),
    protein_g: float | None = Form(None),
    carbs_g: float | None = Form(None),
    fat_g: float | None = Form(None),
    food_image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
) -> DietRecord:
    _get_user_or_404(db)

    image_path: str | None = None
    if food_image is not None:
        os.makedirs(settings.upload_dir, exist_ok=True)
        ext = os.path.splitext(food_image.filename or "image.jpg")[1] or ".jpg"
        filename = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(settings.upload_dir, filename)
        with open(file_path, "wb") as f:
            f.write(await food_image.read())
        image_path = filename

    record = DietRecord(
        user_id=_DEFAULT_USER_ID,
        calorie_intake=calorie_intake,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
        food_image_path=image_path,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    analyze_after_submission(db, _DEFAULT_USER_ID)
    return record


@router.get("/diet", response_model=list[DietRecordRead])
def list_diet(limit: int = 30, db: Session = Depends(get_db)) -> list[DietRecord]:
    return db.scalars(  # type: ignore[return-value]
        select(DietRecord)
        .where(DietRecord.user_id == _DEFAULT_USER_ID)
        .order_by(DietRecord.recorded_at.desc())
        .limit(limit)
    ).all()


# --------------------------------------------------------------------------- #
# Sleep                                                                        #
# --------------------------------------------------------------------------- #

@router.post("/sleep", response_model=SleepRecordRead, status_code=201)
def submit_sleep(
    payload: SleepRecordCreate,
    db: Session = Depends(get_db),
) -> SleepRecord:
    _get_user_or_404(db)
    if payload.wake_time <= payload.sleep_start:
        raise HTTPException(status_code=422, detail="wake_time must be after sleep_start.")
    record = SleepRecord(user_id=_DEFAULT_USER_ID, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    analyze_after_submission(db, _DEFAULT_USER_ID)
    return record


@router.get("/sleep", response_model=list[SleepRecordRead])
def list_sleep(limit: int = 30, db: Session = Depends(get_db)) -> list[SleepRecord]:
    return db.scalars(  # type: ignore[return-value]
        select(SleepRecord)
        .where(SleepRecord.user_id == _DEFAULT_USER_ID)
        .order_by(SleepRecord.sleep_start.desc())
        .limit(limit)
    ).all()


# --------------------------------------------------------------------------- #
# Exercise                                                                     #
# --------------------------------------------------------------------------- #

@router.post("/exercise", response_model=ExerciseRecordRead, status_code=201)
def submit_exercise(
    payload: ExerciseRecordCreate,
    db: Session = Depends(get_db),
) -> ExerciseRecord:
    _get_user_or_404(db)
    met_value = compute_met(
        payload.work_activity_level,
        payload.exercise_type,
        payload.exercise_intensity,
        payload.duration_min,
    )
    record = ExerciseRecord(
        user_id=_DEFAULT_USER_ID,
        met_value=met_value,
        **payload.model_dump(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    analyze_after_submission(db, _DEFAULT_USER_ID)
    return record


@router.get("/exercise", response_model=list[ExerciseRecordRead])
def list_exercise(limit: int = 30, db: Session = Depends(get_db)) -> list[ExerciseRecord]:
    return db.scalars(  # type: ignore[return-value]
        select(ExerciseRecord)
        .where(ExerciseRecord.user_id == _DEFAULT_USER_ID)
        .order_by(ExerciseRecord.recorded_at.desc())
        .limit(limit)
    ).all()


# --------------------------------------------------------------------------- #
# Period                                                                       #
# --------------------------------------------------------------------------- #

@router.post("/period", response_model=PeriodRecordRead, status_code=201)
def submit_period(
    payload: PeriodRecordCreate,
    db: Session = Depends(get_db),
) -> PeriodRecord:
    _get_user_or_404(db)
    record = PeriodRecord(user_id=_DEFAULT_USER_ID, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    analyze_after_submission(db, _DEFAULT_USER_ID)
    return record


@router.get("/period", response_model=list[PeriodRecordRead])
def list_period(limit: int = 30, db: Session = Depends(get_db)) -> list[PeriodRecord]:
    return db.scalars(  # type: ignore[return-value]
        select(PeriodRecord)
        .where(PeriodRecord.user_id == _DEFAULT_USER_ID)
        .order_by(PeriodRecord.recorded_at.desc())
        .limit(limit)
    ).all()
