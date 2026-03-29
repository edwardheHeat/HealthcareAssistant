from __future__ import annotations

from datetime import UTC
from datetime import date as dt_date
from datetime import datetime as dt_datetime
from typing import Literal

from pydantic import BaseModel, Field, computed_field, model_validator

from app.models.health_records import FlowAmount


def _today() -> dt_date:
    return dt_datetime.now(UTC).date()


def _ft_to_cm(height_ft: float) -> float:
    return round(height_ft * 30.48, 2)


def _cm_to_ft(height_cm: float) -> float:
    return round(height_cm / 30.48, 2)


def _lbs_to_kg(weight_lbs: float) -> float:
    return round(weight_lbs * 0.45359237, 2)


def _kg_to_lbs(weight_kg: float) -> float:
    return round(weight_kg / 0.45359237, 2)


def _normalize_intensity(value: str | None) -> Literal["low", "medium", "high"] | None:
    if value is None:
        return None
    normalized = value.lower()
    if normalized == "moderate":
        return "medium"
    if normalized == "very_high":
        return "high"
    if normalized in {"low", "medium", "high"}:
        return normalized
    raise ValueError("intensity must be one of: low, medium, high")


class BasicIndicatorCreate(BaseModel):
    user_id: int = Field(default=1, ge=1)
    date: dt_date = Field(default_factory=_today)
    height_cm: float | None = Field(default=None, gt=0)
    weight_kg: float | None = Field(default=None, gt=0)
    height_ft: float | None = Field(default=None, gt=0)
    weight_lbs: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def normalize_units(self) -> BasicIndicatorCreate:
        if self.height_cm is None:
            if self.height_ft is None:
                raise ValueError("height_cm or height_ft is required")
            self.height_cm = _ft_to_cm(self.height_ft)
        if self.weight_kg is None:
            if self.weight_lbs is None:
                raise ValueError("weight_kg or weight_lbs is required")
            self.weight_kg = _lbs_to_kg(self.weight_lbs)
        return self


class BasicIndicatorRead(BaseModel):
    id: int
    user_id: int
    date: dt_date
    height_cm: float
    weight_kg: float

    model_config = {"from_attributes": True}

    @computed_field(return_type=float)
    def height_ft(self) -> float:
        return _cm_to_ft(self.height_cm)

    @computed_field(return_type=float)
    def weight_lbs(self) -> float:
        return _kg_to_lbs(self.weight_kg)

    @computed_field(return_type=str)
    def recorded_at(self) -> str:
        return self.date.isoformat()


class DietRecordCreate(BaseModel):
    user_id: int = Field(default=1, ge=1)
    date: dt_date = Field(default_factory=_today)
    breakfast_calories: int | None = Field(default=None, ge=0)
    lunch_calories: int | None = Field(default=None, ge=0)
    dinner_calories: int | None = Field(default=None, ge=0)
    calorie_intake: int | None = Field(default=None, ge=0)
    protein_g: float = Field(default=0, ge=0)
    carbs_g: float = Field(default=0, ge=0)
    fat_g: float = Field(default=0, ge=0)

    @model_validator(mode="after")
    def normalize_meals(self) -> DietRecordCreate:
        meals = [
            self.breakfast_calories,
            self.lunch_calories,
            self.dinner_calories,
        ]
        if all(value is None for value in meals):
            if self.calorie_intake is None:
                raise ValueError(
                    "Provide meal calories or a total calorie_intake value"
                )
            shared = self.calorie_intake // 3
            self.breakfast_calories = shared
            self.lunch_calories = shared
            self.dinner_calories = self.calorie_intake - (shared * 2)
        else:
            self.breakfast_calories = self.breakfast_calories or 0
            self.lunch_calories = self.lunch_calories or 0
            self.dinner_calories = self.dinner_calories or 0
        return self


class DietRecordRead(BaseModel):
    id: int
    user_id: int
    date: dt_date
    breakfast_calories: int
    lunch_calories: int
    dinner_calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    food_image_path: str | None = None

    model_config = {"from_attributes": True}

    @computed_field(return_type=int)
    def calorie_intake(self) -> int:
        return self.breakfast_calories + self.lunch_calories + self.dinner_calories

    @computed_field(return_type=str)
    def recorded_at(self) -> str:
        return self.date.isoformat()


class SleepRecordCreate(BaseModel):
    user_id: int = Field(default=1, ge=1)
    date: dt_date | None = None
    sleep_start: dt_datetime
    sleep_end: dt_datetime | None = None
    wake_time: dt_datetime | None = None
    quality: int = Field(default=3, ge=1, le=5)

    @model_validator(mode="after")
    def normalize_sleep_fields(self) -> SleepRecordCreate:
        if self.sleep_end is None:
            if self.wake_time is None:
                raise ValueError("sleep_end or wake_time is required")
            self.sleep_end = self.wake_time
        if self.sleep_end <= self.sleep_start:
            raise ValueError("sleep_end must be after sleep_start")
        if self.date is None:
            self.date = self.sleep_start.date()
        return self


class SleepRecordRead(BaseModel):
    id: int
    user_id: int
    date: dt_date
    sleep_start: dt_datetime
    sleep_end: dt_datetime
    quality: int

    model_config = {"from_attributes": True}

    @computed_field(return_type=dt_datetime)
    def wake_time(self) -> dt_datetime:
        return self.sleep_end


class ExerciseRecordCreate(BaseModel):
    user_id: int = Field(default=1, ge=1)
    date: dt_date = Field(default_factory=_today)
    duration_minutes: int | None = Field(default=None, ge=0, le=1440)
    duration_min: int | None = Field(default=None, ge=0, le=1440)
    intensity: Literal["low", "medium", "high"] | None = None
    exercise_intensity: str | None = None
    exercise_type: str | None = None
    work_activity_level: str | None = None

    @model_validator(mode="after")
    def normalize_exercise_fields(self) -> ExerciseRecordCreate:
        if self.duration_minutes is None:
            if self.duration_min is None:
                raise ValueError("duration_minutes or duration_min is required")
            self.duration_minutes = self.duration_min
        if self.intensity is None:
            self.intensity = _normalize_intensity(self.exercise_intensity)
        if self.intensity is None:
            raise ValueError("intensity or exercise_intensity is required")
        return self


class ExerciseRecordRead(BaseModel):
    id: int
    user_id: int
    date: dt_date
    duration_minutes: int
    intensity: Literal["low", "medium", "high"]

    model_config = {"from_attributes": True}

    @computed_field(return_type=int)
    def duration_min(self) -> int:
        return self.duration_minutes

    @computed_field(return_type=str)
    def exercise_intensity(self) -> str:
        return self.intensity

    @computed_field(return_type=float)
    def met_value(self) -> float:
        intensity_met = {"low": 3.0, "medium": 6.0, "high": 9.0}[self.intensity]
        exercise_hours = self.duration_minutes / 60.0
        rest_hours = max(0.0, 16.0 - exercise_hours)
        return round((intensity_met * exercise_hours + 1.5 * rest_hours) / 16.0, 2)

    @computed_field(return_type=str)
    def recorded_at(self) -> str:
        return self.date.isoformat()


class PeriodRecordCreate(BaseModel):
    has_flow: bool
    flow_amount: FlowAmount | None = None


class PeriodRecordRead(PeriodRecordCreate):
    id: int
    user_id: int
    recorded_at: dt_datetime

    model_config = {"from_attributes": True}
