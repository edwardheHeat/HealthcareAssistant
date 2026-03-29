"""Unit tests for the MET calculator service."""

from app.models.health_records import ExerciseIntensity, WorkActivityLevel
from app.services.met import compute_met


class TestComputeMet:
    def test_known_exercise_running_high(self) -> None:
        met = compute_met(
            WorkActivityLevel.sedentary,
            "running",
            ExerciseIntensity.high,
            60,
        )
        # 1 hour running high: (11.5*1 + 1.5*15)/16 = (11.5+22.5)/16 = 2.125
        assert 2.0 <= met <= 4.0

    def test_known_exercise_yoga_low(self) -> None:
        met = compute_met(
            WorkActivityLevel.sedentary,
            "yoga",
            ExerciseIntensity.low,
            60,
        )
        # 1 hour yoga low: (2.0*1 + 1.5*15)/16 ≈ 1.53
        assert 1.0 <= met <= 3.0

    def test_heavy_work_level_boosts_met(self) -> None:
        met_sed = compute_met(
            WorkActivityLevel.sedentary,
            "walking",
            ExerciseIntensity.low,
            30,
        )
        met_heavy = compute_met(
            WorkActivityLevel.heavy,
            "walking",
            ExerciseIntensity.low,
            30,
        )
        assert met_heavy > met_sed

    def test_longer_duration_changes_met(self) -> None:
        short = compute_met(
            WorkActivityLevel.sedentary,
            "cycling",
            ExerciseIntensity.moderate,
            30,
        )
        long_ = compute_met(
            WorkActivityLevel.sedentary,
            "cycling",
            ExerciseIntensity.moderate,
            120,
        )
        # Both valid; more exercise time should shift MET toward exercise MET (8.0)
        assert short != long_

    def test_unknown_exercise_type_uses_default(self) -> None:
        met = compute_met(
            WorkActivityLevel.sedentary,
            "zorbing",
            ExerciseIntensity.moderate,
            60,
        )
        # Fallback for unknown type, moderate intensity default = 5.0
        assert 1.0 <= met <= 6.0

    def test_zero_duration_returns_only_work_met(self) -> None:
        met = compute_met(
            WorkActivityLevel.sedentary,
            "running",
            ExerciseIntensity.very_high,
            0,
        )
        # 0 exercise hours → all rest at sedentary 1.5
        assert met == 1.5
