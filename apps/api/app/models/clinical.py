from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ClinicalHistory(Base):
    """Mostly static per-user clinical background context.

    One row per user. Updated in place (not append-only).
    """

    __tablename__ = "clinical_histories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_profiles.id"), unique=True, index=True
    )
    # Free-text narratives
    injuries: Mapped[str | None] = mapped_column(Text, nullable=True)
    surgeries: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Hard constraints surfaced to the LLM — e.g. "knee surgery — avoid high impact"
    constraints: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ClinicVisitReport(Base):
    """Summaries of individual clinical visits (append-only)."""

    __tablename__ = "clinic_visit_reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), index=True)
    visit_date: Mapped[date] = mapped_column(Date)
    summary: Mapped[str] = mapped_column(Text)
    raw_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
