from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class IndicatorAnalysis(Base):
    __tablename__ = "indicator_analyses"
    __table_args__ = (
        CheckConstraint(
            "category IN ('basic', 'diet', 'exercise', 'sleep')",
            name="ck_indicator_analyses_category",
        ),
        CheckConstraint(
            "period_type IN ('7d', '30d')",
            name="ck_indicator_analyses_period_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), index=True)
    category: Mapped[str] = mapped_column()
    period_type: Mapped[str] = mapped_column()
    analysis_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class OverallAnalysis(Base):
    __tablename__ = "overall_analyses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), index=True)
    summary_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
