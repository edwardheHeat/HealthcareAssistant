# Re-export all models so that Base.metadata.create_all() picks up every table.
from app.models.alerts import Alert, AlertType  # noqa: F401
from app.models.chat import ChatMessage, ChatSession, MessageRole  # noqa: F401
from app.models.clinical import ClinicalHistory, ClinicVisitReport  # noqa: F401
from app.models.health_records import (  # noqa: F401
    BasicIndicatorRecord,
    DietRecord,
    ExerciseIntensity,
    ExerciseRecord,
    FlowAmount,
    PeriodRecord,
    SleepRecord,
    WorkActivityLevel,
)
from app.models.user import UserProfile  # noqa: F401

__all__ = [
    "UserProfile",
    "BasicIndicatorRecord",
    "DietRecord",
    "SleepRecord",
    "ExerciseRecord",
    "WorkActivityLevel",
    "ExerciseIntensity",
    "PeriodRecord",
    "FlowAmount",
    "ClinicalHistory",
    "ClinicVisitReport",
    "Alert",
    "AlertType",
    "ChatSession",
    "ChatMessage",
    "MessageRole",
]
