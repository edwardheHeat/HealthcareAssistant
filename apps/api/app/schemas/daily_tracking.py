from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class DailyBasicMetricsCreate(BaseModel):
    user_id: int = Field(default=1, ge=1)
    date: date
    height_cm: float = Field(..., gt=0)
    weight_kg: float = Field(..., gt=0)


class DailyBasicMetricsRead(DailyBasicMetricsCreate):
    id: int

    model_config = {"from_attributes": True}


class DailyDietCreate(BaseModel):
    user_id: int = Field(default=1, ge=1)
    date: date
    breakfast_calories: int = Field(..., ge=0)
    lunch_calories: int = Field(..., ge=0)
    dinner_calories: int = Field(..., ge=0)
    protein_g: float = Field(..., ge=0)
    carbs_g: float = Field(..., ge=0)
    fat_g: float = Field(..., ge=0)


class DailyDietRead(DailyDietCreate):
    id: int

    model_config = {"from_attributes": True}


class DailyExerciseCreate(BaseModel):
    user_id: int = Field(default=1, ge=1)
    date: date
    duration_minutes: int = Field(..., ge=0)
    intensity: Literal["low", "medium", "high"]


class DailyExerciseRead(DailyExerciseCreate):
    id: int

    model_config = {"from_attributes": True}


class DailySleepCreate(BaseModel):
    user_id: int = Field(default=1, ge=1)
    date: date
    sleep_start: datetime
    sleep_end: datetime
    quality: int = Field(..., ge=1, le=5)

    @model_validator(mode="after")
    def validate_time_order(self) -> "DailySleepCreate":
        if self.sleep_end <= self.sleep_start:
            raise ValueError("sleep_end must be after sleep_start")
        return self


class DailySleepRead(DailySleepCreate):
    id: int

    model_config = {"from_attributes": True}
