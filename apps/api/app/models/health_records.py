"""SQLAlchemy models for all per-period health data submissions."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class WorkActivityLevel(enum.StrEnum):
    sedentary = "sedentary"  # desk job / mostly sitting
    light = "light"  # teacher, light walking
    moderate = "moderate"  # nurse, retail worker
    heavy = "heavy"  # construction, farming
    very_heavy = "very_heavy"  # lumberjack, elite athlete


class ExerciseIntensity(enum.StrEnum):
    low = "low"
    moderate = "moderate"
    high = "high"
    very_high = "very_high"


class FlowAmount(enum.StrEnum):
    light = "light"
    medium = "medium"
    heavy = "heavy"


class BasicIndicatorRecord(Base):
    __tablename__ = "basic_indicator_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), index=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    height_ft: Mapped[float] = mapped_column(Float)
    weight_lbs: Mapped[float] = mapped_column(Float)


class DietRecord(Base):
    __tablename__ = "diet_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), index=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    calorie_intake: Mapped[float] = mapped_column(Float)
    # Relative path under UPLOAD_DIR; nullable if no photo uploaded
    food_image_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # Nutritional breakdown — filled in by LLM analysis of food image (optional)
    protein_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_g: Mapped[float | None] = mapped_column(Float, nullable=True)


class SleepRecord(Base):
    __tablename__ = "sleep_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), index=True)
    sleep_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    wake_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ExerciseRecord(Base):
    __tablename__ = "exercise_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), index=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    work_activity_level: Mapped[WorkActivityLevel] = mapped_column(
        Enum(WorkActivityLevel, name="work_activity_level")
    )
    # Free-text description: "running", "cycling", "yoga", etc.
    exercise_type: Mapped[str] = mapped_column(String(120))
    exercise_intensity: Mapped[ExerciseIntensity] = mapped_column(
        Enum(ExerciseIntensity, name="exercise_intensity")
    )
    duration_min: Mapped[int] = mapped_column(Integer)
    # Computed MET value stored at submission time (no LLM involved)
    met_value: Mapped[float] = mapped_column(Float)


class PeriodRecord(Base):
    __tablename__ = "period_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), index=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    has_flow: Mapped[bool] = mapped_column()
    flow_amount: Mapped[FlowAmount | None] = mapped_column(
        Enum(FlowAmount, name="flow_amount"), nullable=True
    )
