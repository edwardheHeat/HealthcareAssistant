"""MET (Metabolic Equivalent of Task) calculator.

MET values are computed from standard lookup tables — no LLM involved.
The final met_value stored per ExerciseRecord represents the composite
daily MET accounting for both occupational activity and intentional exercise.
"""

from app.models.health_records import ExerciseIntensity, WorkActivityLevel

# Base occupational MET values (average daily contribution)
_WORK_MET: dict[WorkActivityLevel, float] = {
    WorkActivityLevel.sedentary: 1.5,
    WorkActivityLevel.light: 2.5,
    WorkActivityLevel.moderate: 3.5,
    WorkActivityLevel.heavy: 5.0,
    WorkActivityLevel.very_heavy: 7.0,
}

# Exercise MET lookup: (exercise_type_keyword, intensity) -> MET
# Falls back to intensity default if type keyword not found.
_EXERCISE_MET_TABLE: dict[str, dict[ExerciseIntensity, float]] = {
    "running": {
        ExerciseIntensity.low: 6.0,
        ExerciseIntensity.moderate: 9.0,
        ExerciseIntensity.high: 11.5,
        ExerciseIntensity.very_high: 14.0,
    },
    "cycling": {
        ExerciseIntensity.low: 4.0,
        ExerciseIntensity.moderate: 8.0,
        ExerciseIntensity.high: 10.0,
        ExerciseIntensity.very_high: 12.0,
    },
    "swimming": {
        ExerciseIntensity.low: 5.0,
        ExerciseIntensity.moderate: 7.0,
        ExerciseIntensity.high: 9.5,
        ExerciseIntensity.very_high: 11.0,
    },
    "walking": {
        ExerciseIntensity.low: 2.5,
        ExerciseIntensity.moderate: 3.5,
        ExerciseIntensity.high: 4.5,
        ExerciseIntensity.very_high: 5.5,
    },
    "yoga": {
        ExerciseIntensity.low: 2.0,
        ExerciseIntensity.moderate: 3.0,
        ExerciseIntensity.high: 4.0,
        ExerciseIntensity.very_high: 5.0,
    },
    "weightlifting": {
        ExerciseIntensity.low: 3.0,
        ExerciseIntensity.moderate: 5.0,
        ExerciseIntensity.high: 6.0,
        ExerciseIntensity.very_high: 8.0,
    },
    "hiit": {
        ExerciseIntensity.low: 7.0,
        ExerciseIntensity.moderate: 9.0,
        ExerciseIntensity.high: 12.0,
        ExerciseIntensity.very_high: 14.0,
    },
    "basketball": {
        ExerciseIntensity.low: 4.5,
        ExerciseIntensity.moderate: 6.5,
        ExerciseIntensity.high: 8.0,
        ExerciseIntensity.very_high: 9.0,
    },
    "soccer": {
        ExerciseIntensity.low: 5.0,
        ExerciseIntensity.moderate: 7.0,
        ExerciseIntensity.high: 10.0,
        ExerciseIntensity.very_high: 12.0,
    },
    "tennis": {
        ExerciseIntensity.low: 4.0,
        ExerciseIntensity.moderate: 6.0,
        ExerciseIntensity.high: 8.0,
        ExerciseIntensity.very_high: 10.0,
    },
}

# Fallback MET by intensity when exercise type is unknown
_INTENSITY_DEFAULT: dict[ExerciseIntensity, float] = {
    ExerciseIntensity.low: 3.0,
    ExerciseIntensity.moderate: 5.0,
    ExerciseIntensity.high: 7.0,
    ExerciseIntensity.very_high: 10.0,
}


def compute_met(
    work_level: WorkActivityLevel,
    exercise_type: str,
    intensity: ExerciseIntensity,
    duration_min: int,
) -> float:
    """Compute a composite daily MET value.

    Formula:
        exercise_met × (duration_min / 60) + work_met × (remaining_waking_hours)
    normalised to a single representative daily average MET.

    The result is stored on ExerciseRecord.met_value.
    """
    # Look up exercise MET
    type_key = exercise_type.lower().strip()
    matched_key = next(
        (k for k in _EXERCISE_MET_TABLE if k in type_key),
        None,
    )
    if matched_key:
        exercise_met = _EXERCISE_MET_TABLE[matched_key][intensity]
    else:
        exercise_met = _INTENSITY_DEFAULT[intensity]

    work_met = _WORK_MET[work_level]
    exercise_hours = duration_min / 60.0
    # Assume 16 waking hours total; remaining hours at work/rest level
    rest_hours = max(0.0, 16.0 - exercise_hours)
    daily_met = (exercise_met * exercise_hours + work_met * rest_hours) / 16.0
    return round(daily_met, 2)
