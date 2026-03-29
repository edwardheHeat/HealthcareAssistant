from datetime import date

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ClinicalHistoryEntry(Base):
    __tablename__ = "clinical_history_entries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), index=True)
    illness_name: Mapped[str] = mapped_column(String(120))
    diagnosis_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    medication: Mapped[str | None] = mapped_column(Text, nullable=True)


class VaccineRecord(Base):
    __tablename__ = "vaccine_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), index=True)
    vaccine_name: Mapped[str] = mapped_column(String(120))
    date_administered: Mapped[date] = mapped_column(Date)


class HealthAlert(Base):
    __tablename__ = "health_alerts"
    __table_args__ = (
        Index("ix_health_alerts_user_date", "user_id", "date"),
        CheckConstraint(
            "severity IN ('low', 'medium', 'high')",
            name="ck_health_alerts_severity",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), index=True)
    date: Mapped[date] = mapped_column(Date)
    alert_type: Mapped[str] = mapped_column(String(80))
    severity: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(Text)
