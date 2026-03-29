import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AlertType(str, enum.Enum):
    abnormal = "abnormal"  # metric out of healthy range
    stale = "stale"  # metric not updated in too long


class AlertSeverity(str, enum.Enum):
    warning = "warning"
    critical = "critical"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    alert_type: Mapped[AlertType] = mapped_column(
        Enum(AlertType, name="alert_type")
    )
    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity, name="alert_severity"),
        default=AlertSeverity.warning,
    )
    # Which metric triggered this: "weight", "sleep", "calories", etc.
    metric: Mapped[str] = mapped_column(String(80))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
