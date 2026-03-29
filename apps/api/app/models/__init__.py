# Re-export all models so that Base.metadata.create_all() picks up every table.
from app.models.alerts import Alert, AlertType
from app.models.analysis import IndicatorAnalysis, OverallAnalysis
from app.models.chat import ChatMessage, ChatSession, MessageRole
from app.models.clinical import ClinicalHistory, ClinicVisitReport
from app.models.daily_tracking import (
    DailyBasicMetrics,
    DailyDiet,
    DailyExercise,
    DailySleep,
)
from app.models.health_records import (
    BasicIndicatorRecord,
    DietRecord,
    ExerciseIntensity,
    ExerciseRecord,
    FlowAmount,
    PeriodRecord,
    SleepRecord,
    WorkActivityLevel,
)
from app.models.medical import ClinicalHistoryEntry, HealthAlert, VaccineRecord
from app.models.reproductive import PeriodCycle, PeriodCycleSummary
from app.models.user import UserProfile

__all__ = [
    "Alert",
    "AlertType",
    "BasicIndicatorRecord",
    "ChatMessage",
    "ChatSession",
    "ClinicVisitReport",
    "ClinicalHistory",
    "ClinicalHistoryEntry",
    "DailyBasicMetrics",
    "DailyDiet",
    "DailyExercise",
    "DailySleep",
    "DietRecord",
    "ExerciseIntensity",
    "ExerciseRecord",
    "FlowAmount",
    "HealthAlert",
    "IndicatorAnalysis",
    "MessageRole",
    "OverallAnalysis",
    "PeriodCycle",
    "PeriodCycleSummary",
    "PeriodRecord",
    "SleepRecord",
    "UserProfile",
    "VaccineRecord",
    "WorkActivityLevel",
]
