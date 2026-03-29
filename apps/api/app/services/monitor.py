"""Health monitor service — redesigned.

Entry point: trigger_monitor(db, user_id, snapshot)

The monitor accepts a typed MonitorSnapshot built by the router after
saving a health record. It:
  1. Runs the check function for the submitted metric.
  2. Collects AbnormalFinding objects from immediate and/or trend checks.
  3. If findings exist, calls the LLM alert writer to generate a message.
  4. Persists one Alert row and returns it (or None if clean).
"""

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
