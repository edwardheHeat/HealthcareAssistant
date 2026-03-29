
"""Health monitor service — redesigned.

Entry point: trigger_monitor(db, user_id, snapshot)

The monitor accepts a typed MonitorSnapshot built by the router after
saving a health record. It:
  1. Runs the check function for the submitted metric.
  2. Collects AbnormalFinding objects from immediate and/or trend checks.
  3. If findings exist, calls the LLM alert writer to generate a message.
  4. Persists one Alert row and returns it (or None if clean).
"""


"""Health monitor service."""

from datetime import UTC, date, datetime

from sqlalchemy import select

from sqlalchemy.orm import Session
from datetime import date


from app.llm.alert_writer import AbnormalFinding, generate_alert_message
from app.models.alerts import Alert, AlertSeverity, AlertType
from app.models.user import UserProfile
from app.services.monitor_types import (
    BasicIndicatorSnapshot,
    DietSnapshot,
    ExerciseSnapshot,
    MonitorSnapshot,
    PeriodSnapshot,
    SleepSnapshot,
)
from app.models.alerts import Alert, AlertType
from app.models.daily_tracking import (
    DailyBasicMetrics,
    DailyDiet,
    DailyExercise,
    DailySleep,

)
from app.models.health_records import PeriodRecord


# ---------------------------------------------------------------------------
# Per-indicator check functions
# Evaluation mode is documented per function.
# Return None if no abnormality is found.
# ---------------------------------------------------------------------------

# ---- Basic Indicators ------------------------------------------------------

def check_bmi(snapshot: BasicIndicatorSnapshot) -> AbnormalFinding | None:
    """IMMEDIATE — flag BMI outside healthy range on every submission."""
    if snapshot.current_height_cm <= 0 or snapshot.current_weight_kg <= 0:
        return None  # Bad data
        
    bmi = snapshot.current_weight_kg / ((snapshot.current_height_cm / 100) ** 2)
    
    if bmi < 17.0:
        return AbnormalFinding("basic_indicators", "critical", "immediate", f"BMI is {bmi:.1f} (severe underweight)")
    elif bmi < 18.5:
        return AbnormalFinding("basic_indicators", "warning", "immediate", f"BMI is {bmi:.1f} (underweight)")
    elif bmi >= 35.0:
        return AbnormalFinding("basic_indicators", "critical", "immediate", f"BMI is {bmi:.1f} (severe obesity)")
    elif bmi >= 30.0:
        return AbnormalFinding("basic_indicators", "warning", "immediate", f"BMI is {bmi:.1f} (obesity)")
        
    return None

def check_height_consistency(snapshot: BasicIndicatorSnapshot) -> AbnormalFinding | None:
    """IMMEDIATE — flag drastic height changes (e.g. tracking error or health issue)."""
    if snapshot.previous_height_cm is None or snapshot.previous_height_cm <= 0:
        return None
        
    # Flag if height changes by more than 3 cm (1.2 inches) for an adult
    delta = abs(snapshot.current_height_cm - snapshot.previous_height_cm)
    if delta > 3.0:
        return AbnormalFinding(
            "basic_indicators", "warning", "immediate", 
            f"Drastic height change detected: {snapshot.previous_height_cm:.1f}cm to {snapshot.current_height_cm:.1f}cm"
        )
    return None

def check_weight_change(snapshot: BasicIndicatorSnapshot) -> AbnormalFinding | None:
    """TREND (30d) — flag rapid weight change or sustained gaining/losing trend."""
    if snapshot.previous_weight_kg is None or snapshot.previous_weight_kg <= 0:
        return None
        
    delta_kg = snapshot.current_weight_kg - snapshot.previous_weight_kg
    trend = snapshot.trend_stats.get("weight_trend")
    
    # Alert if weight changes by > 3.0 kg structurally
    if delta_kg > 3.0 and trend == "gaining":
        return AbnormalFinding("basic_indicators", "warning", "trend", f"Rapid weight gain: +{delta_kg:.1f}kg with sustained trend")
    elif delta_kg < -3.0 and trend == "losing":
        return AbnormalFinding("basic_indicators", "warning", "trend", f"Rapid weight loss: {delta_kg:.1f}kg with sustained trend")
        
    return None

# ---- Diet ------------------------------------------------------------------

def check_calories_absolute(snapshot: DietSnapshot) -> AbnormalFinding | None:
    """IMMEDIATE — flag dangerously low or high calorie intake."""
    cal = snapshot.current_calories
    if cal <= 0:
        return None
        
    if cal < 800:
        return AbnormalFinding("diet", "critical", "immediate", f"Dangerously low calories: {cal} kcal")
    elif cal > 4000:
        return AbnormalFinding("diet", "warning", "immediate", f"Very high calorie intake: {cal} kcal")
    return None

def check_calorie_trend(snapshot: DietSnapshot) -> AbnormalFinding | None:
    """TREND (7d) — flag sustained large deficit or surplus vs TDEE."""
    diet_stats = snapshot.trend_stats.get("diet", {})
    surplus = diet_stats.get("calorie_deficit_surplus_vs_tdee")
    
    if surplus is None:
        return None
        
    if surplus < -700:
        return AbnormalFinding("diet", "warning", "trend", f"Sustained severe deficit: {surplus} kcal/day (7d avg)")
    elif surplus > 500:
        return AbnormalFinding("diet", "warning", "trend", f"Sustained large surplus: +{surplus} kcal/day (7d avg)")
    return None

# ---- Sleep -----------------------------------------------------------------

def check_sleep_duration(snapshot: SleepSnapshot) -> AbnormalFinding | None:
    """IMMEDIATE — flag a single night with severely abnormal sleep duration."""
    dur = snapshot.current_duration_hrs
    if dur <= 0:
        return None
        
    if dur < 5.0:
        return AbnormalFinding("sleep", "critical", "immediate", f"Critically short sleep: {dur:.1f} hrs")
    elif dur > 10.0:
        return AbnormalFinding("sleep", "warning", "immediate", f"Excessively long sleep: {dur:.1f} hrs")
    return None

def check_sleep_quality(snapshot: SleepSnapshot) -> AbnormalFinding | None:
    """TREND (7d) — flag unusually poor sleep quality over tracking period."""
    avg_quality = snapshot.trend_stats.get("sleep", {}).get("avg_quality_7d")
    if avg_quality is None:
        return None
        
    if avg_quality < 2.5:
        return AbnormalFinding("sleep", "warning", "trend", f"Poor 7-day sleep quality average ({avg_quality:.1f}/5)")
    return None

def check_sleep_consistency(snapshot: SleepSnapshot) -> AbnormalFinding | None:
    """TREND (7d) — flag a significant drop in sleep schedule consistency."""
    score = snapshot.trend_stats.get("sleep", {}).get("sleep_consistency_score")
    if score is None:
        return None
        
    if score < 40:
        return AbnormalFinding("sleep", "warning", "trend", f"Erratic sleep schedule (consistency score: {score:.1f}/100)")
    return None

# ---- Exercise --------------------------------------------------------------

def check_exercise_frequency(snapshot: ExerciseSnapshot) -> AbnormalFinding | None:
    """TREND (7d vs 30d) — flag sustained decline in exercise frequency."""
    days_7d = snapshot.exercise_days_7d
    avg_30d = snapshot.exercise_days_30d_avg_per_week
    
    if avg_30d >= 3.0 and days_7d <= 1:
        return AbnormalFinding(
            "exercise", "warning", "trend", 
            f"Exercise frequency dropped to {days_7d} days this week (usually {avg_30d:.1f} days/wk)"
        )
    return None

# ---- Period ----------------------------------------------------------------

def check_cycle_phase(snapshot: PeriodSnapshot) -> AbnormalFinding | None:
    """IMMEDIATE — flag overly long cycles or other concerns."""
    if not snapshot.start_date:
        return None
        
    end = snapshot.end_date or date.today()
    duration_days = (end - snapshot.start_date).days
    
    if duration_days > 8:
        return AbnormalFinding("period", "warning", "immediate", f"Abnormally long period flow: {duration_days} days")
    return None

# ---------------------------------------------------------------------------
# Indicator dispatch table
# ---------------------------------------------------------------------------

_CHECKS: dict[str, list] = {
    "basic_indicators": [check_bmi, check_height_consistency, check_weight_change],
    "diet": [check_calories_absolute, check_calorie_trend],
    "sleep": [check_sleep_duration, check_sleep_quality, check_sleep_consistency],
    "exercise": [check_exercise_frequency],
    "period": [check_cycle_phase],
}
_NOW = lambda: datetime.now(tz=UTC)  # noqa: E731

_STALE_THRESHOLDS: dict[str, int] = {
    "basic_indicators": 7,
    "diet": 3,
    "sleep": 3,
    "exercise": 7,
    "period": 14,

}

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def trigger_monitor(
    db: Session,
    user_id: int,
    snapshot: MonitorSnapshot,
) -> Alert | None:
    """Run monitor checks for the submitted metric. Returns the created Alert or None."""
    check_fns = _CHECKS.get(snapshot.metric, [])
    findings: list[AbnormalFinding] = []

    for fn in check_fns:
        result = fn(snapshot)
        if result is not None:
            findings.append(result)

    if not findings:
        return None

    overall_severity = AlertSeverity.critical if any(
        f.severity == "critical" for f in findings
    ) else AlertSeverity.warning

    user = db.get(UserProfile, user_id)
    if user is None:
        return None

    message = await generate_alert_message(findings, user)

    alert = Alert(
        user_id=user_id,
        alert_type=AlertType.abnormal,
        severity=overall_severity,
        metric=snapshot.metric,
        message=message,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

def _as_datetime(value: date | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    return datetime.combine(value, datetime.min.time(), tzinfo=UTC)


def _daily_exercise_met(duration_minutes: int, intensity: str) -> float:
    intensity_met = {"low": 3.0, "medium": 6.0, "high": 9.0}[intensity]
    exercise_hours = duration_minutes / 60.0
    rest_hours = max(0.0, 16.0 - exercise_hours)
    return (intensity_met * exercise_hours + 1.5 * rest_hours) / 16.0


def _add_alert(
    db: Session,
    user_id: int,
    alert_type: AlertType,
    metric: str,
    message: str,
) -> None:
    existing = db.scalars(
        select(Alert).where(
            Alert.user_id == user_id,
            Alert.metric == metric,
            Alert.alert_type == alert_type,
            Alert.is_read == False,  # noqa: E712
        )
    ).first()
    if existing:
        return
    db.add(
        Alert(
            user_id=user_id,
            alert_type=alert_type,
            metric=metric,
            message=message,
        )
    )


def _check_stale(db: Session, user_id: int) -> None:
    now = _NOW()
    checks: list[tuple[str, datetime | None]] = [
        (
            "basic_indicators",
            _as_datetime(
                db.scalars(
                    select(DailyBasicMetrics.date)
                    .where(DailyBasicMetrics.user_id == user_id)
                    .order_by(DailyBasicMetrics.date.desc())
                    .limit(1)
                ).first()
            ),
        ),
        (
            "diet",
            _as_datetime(
                db.scalars(
                    select(DailyDiet.date)
                    .where(DailyDiet.user_id == user_id)
                    .order_by(DailyDiet.date.desc())
                    .limit(1)
                ).first()
            ),
        ),
        (
            "sleep",
            _as_datetime(
                db.scalars(
                    select(DailySleep.date)
                    .where(DailySleep.user_id == user_id)
                    .order_by(DailySleep.date.desc())
                    .limit(1)
                ).first()
            ),
        ),
        (
            "exercise",
            _as_datetime(
                db.scalars(
                    select(DailyExercise.date)
                    .where(DailyExercise.user_id == user_id)
                    .order_by(DailyExercise.date.desc())
                    .limit(1)
                ).first()
            ),
        ),
        (
            "period",
            _as_datetime(
                db.scalars(
                    select(PeriodRecord.recorded_at)
                    .where(PeriodRecord.user_id == user_id)
                    .order_by(PeriodRecord.recorded_at.desc())
                    .limit(1)
                ).first()
            ),
        ),
    ]

    for metric, last_at in checks:
        threshold_days = _STALE_THRESHOLDS[metric]
        if last_at is None:
            days_old = threshold_days + 1
        else:
            days_old = (now - last_at).days

        if days_old >= threshold_days:
            _add_alert(
                db,
                user_id,
                AlertType.stale,
                metric,
                f"Your {metric.replace('_', ' ')} has not been updated "
                f"in {days_old} day(s). "
                f"Please log your data to keep your health profile accurate.",
            )


def _check_abnormal(db: Session, user_id: int) -> None:
    latest_basic = db.scalars(
        select(DailyBasicMetrics)
        .where(DailyBasicMetrics.user_id == user_id)
        .order_by(DailyBasicMetrics.date.desc())
        .limit(1)
    ).first()
    if latest_basic:
        height_m = latest_basic.height_cm / 100.0
        bmi = latest_basic.weight_kg / (height_m**2) if height_m else 0
        if bmi > 0 and (bmi < 18.5 or bmi > 30):
            category = "underweight" if bmi < 18.5 else "obese range"
            _add_alert(
                db,
                user_id,
                AlertType.abnormal,
                "bmi",
                f"Your current BMI is {bmi:.1f}, which falls in the {category}. "
                "Consider consulting a healthcare provider.",
            )

    latest_sleep = db.scalars(
        select(DailySleep)
        .where(DailySleep.user_id == user_id)
        .order_by(DailySleep.date.desc())
        .limit(1)
    ).first()
    if latest_sleep:
        hours = (
            latest_sleep.sleep_end - latest_sleep.sleep_start
        ).total_seconds() / 3600
        if hours < 5.0:
            _add_alert(
                db,
                user_id,
                AlertType.abnormal,
                "sleep",
                f"You slept only {hours:.1f} hours last night, "
                "well below the recommended 7 to 9 hours.",
            )
        elif hours > 10.0:
            _add_alert(
                db,
                user_id,
                AlertType.abnormal,
                "sleep",
                f"You slept {hours:.1f} hours last night. "
                "Consistently sleeping over 10 hours may indicate an "
                "underlying issue.",
            )

    latest_diet = db.scalars(
        select(DailyDiet)
        .where(DailyDiet.user_id == user_id)
        .order_by(DailyDiet.date.desc())
        .limit(1)
    ).first()
    if latest_diet:
        calories = (
            latest_diet.breakfast_calories
            + latest_diet.lunch_calories
            + latest_diet.dinner_calories
        )
        if calories < 1000:
            _add_alert(
                db,
                user_id,
                AlertType.abnormal,
                "calories",
                f"Your logged calorie intake ({calories:.0f} kcal) "
                "is very low. Severe calorie restriction can be harmful.",
            )
        elif calories > 5000:
            _add_alert(
                db,
                user_id,
                AlertType.abnormal,
                "calories",
                f"Your logged calorie intake ({calories:.0f} kcal) "
                "is unusually high. If this is sustained, it may impact "
                "your health goals.",
            )

    latest_exercise = db.scalars(
        select(DailyExercise)
        .where(DailyExercise.user_id == user_id)
        .order_by(DailyExercise.date.desc())
        .limit(1)
    ).first()
    if latest_exercise:
        met_value = _daily_exercise_met(
            latest_exercise.duration_minutes,
            latest_exercise.intensity,
        )
        if met_value > 8.0 and latest_exercise.duration_minutes > 180:
            _add_alert(
                db,
                user_id,
                AlertType.abnormal,
                "exercise",
                "Your recent exercise load was unusually intense and "
                "prolonged. Make sure you are recovering adequately.",
            )


def run_monitor(db: Session, user_id: int) -> list[Alert]:
    before_ids = set(db.scalars(select(Alert.id).where(Alert.user_id == user_id)).all())
    _check_stale(db, user_id)
    _check_abnormal(db, user_id)
    db.commit()
    after_ids = set(db.scalars(select(Alert.id).where(Alert.user_id == user_id)).all())
    new_ids = after_ids - before_ids
    return db.scalars(select(Alert).where(Alert.id.in_(new_ids))).all()

