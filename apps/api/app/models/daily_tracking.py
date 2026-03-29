from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class DailyBasicMetrics(Base):
    __tablename__ = "daily_basic_metrics"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_daily_basic_metrics_user_date"),
        Index("ix_daily_basic_metrics_user_date", "user_id", "date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), index=True)
    date: Mapped[date] = mapped_column(Date)
    height_cm: Mapped[float] = mapped_column(Float)
    weight_kg: Mapped[float] = mapped_column(Float)


class DailyDiet(Base):
    __tablename__ = "daily_diet"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_daily_diet_user_date"),
        Index("ix_daily_diet_user_date", "user_id", "date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), index=True)
    date: Mapped[date] = mapped_column(Date)
    breakfast_calories: Mapped[int] = mapped_column(Integer)
    lunch_calories: Mapped[int] = mapped_column(Integer)
    dinner_calories: Mapped[int] = mapped_column(Integer)
    protein_g: Mapped[float] = mapped_column(Float)
    carbs_g: Mapped[float] = mapped_column(Float)
    fat_g: Mapped[float] = mapped_column(Float)


class DailyExercise(Base):
    __tablename__ = "daily_exercise"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_daily_exercise_user_date"),
        Index("ix_daily_exercise_user_date", "user_id", "date"),
        CheckConstraint(
            "intensity IN ('low', 'medium', 'high')",
            name="ck_daily_exercise_intensity",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), index=True)
    date: Mapped[date] = mapped_column(Date)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    intensity: Mapped[str] = mapped_column()


class DailySleep(Base):
    __tablename__ = "daily_sleep"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_daily_sleep_user_date"),
        Index("ix_daily_sleep_user_date", "user_id", "date"),
        CheckConstraint("quality BETWEEN 1 AND 5", name="ck_daily_sleep_quality"),
        CheckConstraint("sleep_end > sleep_start", name="ck_daily_sleep_time_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), index=True)
    date: Mapped[date] = mapped_column(Date)
    sleep_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    sleep_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    quality: Mapped[int] = mapped_column(Integer)
