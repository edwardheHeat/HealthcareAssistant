from datetime import datetime

from pydantic import BaseModel, Field

from app.models.health_records import ExerciseIntensity, FlowAmount, WorkActivityLevel


# --- Basic Indicators ---

class BasicIndicatorCreate(BaseModel):
    height_ft: float = Field(..., gt=0, le=10)
    weight_lbs: float = Field(..., gt=0, le=1500)


class BasicIndicatorRead(BasicIndicatorCreate):
    id: int
    user_id: int
    recorded_at: datetime

    model_config = {"from_attributes": True}


# --- Diet ---

class DietRecordCreate(BaseModel):
    calorie_intake: float = Field(..., ge=0, le=20000)
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None


class DietRecordRead(DietRecordCreate):
    id: int
    user_id: int
    recorded_at: datetime
    food_image_path: str | None

    model_config = {"from_attributes": True}


# --- Sleep ---

class SleepRecordCreate(BaseModel):
    sleep_start: datetime
    wake_time: datetime


class SleepRecordRead(SleepRecordCreate):
    id: int
    user_id: int

    model_config = {"from_attributes": True}


# --- Exercise ---

class ExerciseRecordCreate(BaseModel):
    work_activity_level: WorkActivityLevel
    exercise_type: str = Field(..., max_length=120)
    exercise_intensity: ExerciseIntensity
    duration_min: int = Field(..., ge=0, le=1440)


class ExerciseRecordRead(ExerciseRecordCreate):
    id: int
    user_id: int
    recorded_at: datetime
    met_value: float

    model_config = {"from_attributes": True}


# --- Period ---

class PeriodRecordCreate(BaseModel):
    has_flow: bool
    flow_amount: FlowAmount | None = None


class PeriodRecordRead(PeriodRecordCreate):
    id: int
    user_id: int
    recorded_at: datetime

    model_config = {"from_attributes": True}
