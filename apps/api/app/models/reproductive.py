from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class PeriodCycle(Base):
    __tablename__ = "period_cycles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), index=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)


class PeriodCycleSummary(Base):
    __tablename__ = "period_cycle_summaries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), index=True)
    avg_cycle_length_days: Mapped[float] = mapped_column(Float)
    predicted_next_start_start: Mapped[date] = mapped_column(Date)
    predicted_next_start_end: Mapped[date] = mapped_column(Date)
    analysis_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
