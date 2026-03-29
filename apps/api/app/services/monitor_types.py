"""Typed snapshot dataclasses for the monitor service.

Each snapshot carries exactly the fields the corresponding check functions
need — no extra DB queries inside the monitor itself.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Literal


# ---------------------------------------------------------------------------
# Per-metric snapshot types
# ---------------------------------------------------------------------------

@dataclass
class BasicIndicatorSnapshot:
    """Snapshot for a new basic-indicators submission."""

    metric: Literal["basic_indicators"] = "basic_indicators"
    current_height_cm: float = 0.0
    previous_height_cm: float | None = None
    current_weight_kg: float = 0.0
    # Weight of the record immediately before this one (None = first ever)
    previous_weight_kg: float | None = None
    # Populated from build_user_stats_context()
    # Relevant keys: bmi, weight_trend
    trend_stats: dict = field(default_factory=dict)


@dataclass
class DietSnapshot:
    """Snapshot for a new diet record submission."""

    metric: Literal["diet"] = "diet"
    current_calories: float = 0.0
    # Relevant trend_stats keys:
    #   diet.avg_calories_7d, diet.calorie_deficit_surplus_vs_tdee
    trend_stats: dict = field(default_factory=dict)


@dataclass
class SleepSnapshot:
    """Snapshot for a new sleep record submission."""

    metric: Literal["sleep"] = "sleep"
    current_duration_hrs: float = 0.0
    current_quality: int = 0  # e.g., 1-5 scale (keep for future use)
    # Duration of the record immediately before this one
    previous_duration_hrs: float | None = None
    # Relevant trend_stats keys:
    #   sleep.avg_duration_hrs_7d
    #   sleep.sleep_consistency_score
    #   sleep.avg_quality_7d
    trend_stats: dict = field(default_factory=dict)


@dataclass
class ExerciseSnapshot:
    """Snapshot for a new exercise record submission."""

    metric: Literal["exercise"] = "exercise"
    # To check 7-day vs 30-day frequency
    exercise_days_7d: int = 0
    exercise_days_30d_avg_per_week: float = 0.0
    
    trend_stats: dict = field(default_factory=dict)


@dataclass
class PeriodSnapshot:
    """Snapshot for a period event."""

    metric: Literal["period"] = "period"
    start_date: date | None = None
    end_date: date | None = None
    # Relevant trend_stats keys: period.cycle_phase
    trend_stats: dict = field(default_factory=dict)


# Union type used by the monitor entry point
MonitorSnapshot = (
    BasicIndicatorSnapshot
    | DietSnapshot
    | SleepSnapshot
    | ExerciseSnapshot
    | PeriodSnapshot
)
