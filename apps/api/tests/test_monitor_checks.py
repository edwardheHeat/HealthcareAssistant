"""Tests for per-indicator check functions in services/monitor.py.

All check functions are currently stubs (return None).
This file defines the expected behaviour so you can fill in the
algorithm bodies and see the tests go green.

Run:
    cd apps/api
    LLM_BASE_URL=x LLM_API_KEY=x LLM_MODEL=x pytest tests/test_monitor_checks.py -v
"""

import pytest

from datetime import date, timedelta
from app.services.monitor import (
    check_bmi,
    check_calories_absolute,
    check_calorie_trend,
    check_cycle_phase,
    check_exercise_frequency,
    check_height_consistency,
    check_sleep_consistency,
    check_sleep_duration,
    check_sleep_quality,
    check_weight_change,
)
from app.services.monitor_types import (
    BasicIndicatorSnapshot,
    DietSnapshot,
    ExerciseSnapshot,
    PeriodSnapshot,
    SleepSnapshot,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bi(weight: float, height: float = 170.0, prev_height: float | None = 170.0, prev_weight: float | None = None, trend: str = "stable") -> BasicIndicatorSnapshot:
    return BasicIndicatorSnapshot(
        current_height_cm=height,
        previous_height_cm=prev_height,
        current_weight_kg=weight,
        previous_weight_kg=prev_weight,
        trend_stats={"weight_trend": trend},
    )


def _diet(calories: float, avg_7d: float | None = None, surplus: float | None = None) -> DietSnapshot:
    return DietSnapshot(
        current_calories=calories,
        trend_stats={
            "diet": {
                "avg_calories_7d": avg_7d,
                "calorie_deficit_surplus_vs_tdee": surplus,
            }
        },
    )


def _sleep(hours: float, quality: int = 4, prev: float | None = None, consistency: float | None = 80.0) -> SleepSnapshot:
    return SleepSnapshot(
        current_duration_hrs=hours,
        current_quality=quality,
        previous_duration_hrs=prev,
        trend_stats={"sleep": {
            "avg_duration_hrs_7d": hours, 
            "sleep_consistency_score": consistency,
            "avg_quality_7d": quality
        }},
    )


def _exercise(days_7d: int, avg_weekly_30d: float) -> ExerciseSnapshot:
    return ExerciseSnapshot(
        exercise_days_7d=days_7d,
        exercise_days_30d_avg_per_week=avg_weekly_30d,
        trend_stats={},
    )


def _period(start_days_ago: int, end_days_ago: int | None = None) -> PeriodSnapshot:
    today = date.today()
    return PeriodSnapshot(
        start_date=today - timedelta(days=start_days_ago),
        end_date=(today - timedelta(days=end_days_ago)) if end_days_ago is not None else None,
        trend_stats={},
    )


# ---------------------------------------------------------------------------
# check_bmi  (IMMEDIATE)
# ---------------------------------------------------------------------------

class TestCheckBmi:
    def test_normal_bmi_returns_none(self) -> None:
        # 170cm, 65kg -> BMI ≈ 22.5 (Healthy)
        result = check_bmi(_bi(weight=65.0, height=170.0))
        assert result is None

    def test_underweight_returns_finding(self) -> None:
        # 170cm, 45kg -> BMI ≈ 15.5 (Underweight / Critical)
        result = check_bmi(_bi(weight=45.0, height=170.0))
        assert result is not None
        assert result.metric == "basic_indicators"

    def test_obese_returns_warning(self) -> None:
        # 170cm, 90kg -> BMI ≈ 31.1 (Obese / Warning)
        result = check_bmi(_bi(weight=90.0, height=170.0))
        assert result is not None
        assert result.severity in ("warning", "critical")


# ---------------------------------------------------------------------------
# check_height_consistency (IMMEDIATE)
# ---------------------------------------------------------------------------

class TestCheckHeightConsistency:
    def test_stable_height_returns_none(self) -> None:
        result = check_height_consistency(_bi(65.0, height=170.0, prev_height=170.0))
        assert result is None
        
    def test_missing_prev_height_returns_none(self) -> None:
        result = check_height_consistency(_bi(65.0, height=170.0, prev_height=None))
        assert result is None
        
    def test_drastic_height_change_returns_warning(self) -> None:
        result = check_height_consistency(_bi(65.0, height=175.0, prev_height=170.0))
        assert result is not None
        assert "Drastic height change" in result.raw_description


# ---------------------------------------------------------------------------
# check_weight_change  (TREND / 30d)
# ---------------------------------------------------------------------------

class TestCheckWeightChange:
    def test_stable_weight_returns_none(self) -> None:
        result = check_weight_change(_bi(weight=70.0, prev_weight=69.8, trend="stable"))
        assert result is None

    def test_gaining_trend_with_large_delta_returns_finding(self) -> None:
        # +5 kg delta
        result = check_weight_change(_bi(weight=75.0, prev_weight=70.0, trend="gaining"))
        assert result is not None


# ---------------------------------------------------------------------------
# check_calories_absolute  (IMMEDIATE)
# ---------------------------------------------------------------------------

class TestCheckCaloriesAbsolute:
    def test_normal_calories_returns_none(self) -> None:
        result = check_calories_absolute(_diet(calories=2000))
        assert result is None

    def test_very_low_calories_returns_critical(self) -> None:
        result = check_calories_absolute(_diet(calories=600))
        assert result is not None
        assert result.severity == "critical"

# ---------------------------------------------------------------------------
# check_calorie_trend  (TREND / 7d)
# ---------------------------------------------------------------------------

class TestCheckCalorieTrend:
    def test_balanced_returns_none(self) -> None:
        result = check_calorie_trend(_diet(calories=2000, avg_7d=2000, surplus=50))
        assert result is None

    def test_large_sustained_deficit_returns_finding(self) -> None:
        result = check_calorie_trend(_diet(calories=1400, avg_7d=1400, surplus=-800))
        assert result is not None


# ---------------------------------------------------------------------------
# check_sleep_duration  (IMMEDIATE)
# ---------------------------------------------------------------------------

class TestCheckSleepDuration:
    def test_normal_sleep_returns_none(self) -> None:
        result = check_sleep_duration(_sleep(hours=7.5))
        assert result is None

    def test_critically_short_sleep_returns_critical(self) -> None:
        result = check_sleep_duration(_sleep(hours=3.5))
        assert result is not None
        assert result.severity == "critical"


# ---------------------------------------------------------------------------
# check_sleep_quality  (IMMEDIATE)
# ---------------------------------------------------------------------------

class TestCheckSleepQuality:
    def test_good_quality_returns_none(self) -> None:
        result = check_sleep_quality(_sleep(hours=7.5, quality=4))
        assert result is None
        
    def test_missing_quality_returns_none(self) -> None:
        snap = _sleep(hours=7.5, quality=4)
        snap.trend_stats["sleep"].pop("avg_quality_7d")
        result = check_sleep_quality(snap)
        assert result is None

    def test_poor_quality_returns_warning(self) -> None:
        result = check_sleep_quality(_sleep(hours=7.0, quality=1))
        assert result is not None
        assert result.severity == "warning"


# ---------------------------------------------------------------------------
# check_sleep_consistency  (TREND / 7d)
# ---------------------------------------------------------------------------

class TestCheckSleepConsistency:
    def test_high_consistency_returns_none(self) -> None:
        result = check_sleep_consistency(_sleep(hours=7.5, consistency=85))
        assert result is None


# ---------------------------------------------------------------------------
# check_exercise_frequency  (TREND / 7d vs 30d)
# ---------------------------------------------------------------------------

class TestCheckExerciseFrequency:
    def test_matching_frequency_returns_none(self) -> None:
        # Worked out 3 times this week, usually works out 3 times a week (stable)
        result = check_exercise_frequency(_exercise(days_7d=3, avg_weekly_30d=3.0))
        assert result is None

    def test_declining_frequency_returns_finding(self) -> None:
        # Worked out 0 times this week, but 30d avg is 4 times a week
        result = check_exercise_frequency(_exercise(days_7d=0, avg_weekly_30d=4.0))
        assert result is not None
        assert result.evaluation_mode == "trend"


# ---------------------------------------------------------------------------
# check_cycle_phase  (IMMEDIATE)
# ---------------------------------------------------------------------------

class TestCheckCyclePhase:
    def test_normal_cycle_returns_none(self) -> None:
        result = check_cycle_phase(_period(start_days_ago=4, end_days_ago=None))
        assert result is None

    def test_overly_long_flow_returns_warning(self) -> None:
        # Flow started 15 days ago and is still going (no end_date)
        result = check_cycle_phase(_period(start_days_ago=15, end_days_ago=None))
        assert result is not None
        assert result.severity == "warning"
