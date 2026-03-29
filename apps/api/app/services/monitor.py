"""Health monitor service.

run_monitor() checks the latest health data for:
  1. Abnormal readings (values outside healthy thresholds).
  2. Stale data   (a metric not updated within the expected window).

It writes Alert rows but does NOT send push notifications — the frontend
polls /api/v1/alerts for unread alerts.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alerts import Alert, AlertType
from app.models.health_records import (
    BasicIndicatorRecord,
    DietRecord,
    ExerciseRecord,
    PeriodRecord,
    SleepRecord,
)

_NOW = lambda: datetime.now(tz=timezone.utc)  # noqa: E731

# --- Stale data thresholds (days before an alert fires) ---
_STALE_THRESHOLDS: dict[str, int] = {
    "basic_indicators": 7,
    "diet": 3,
    "sleep": 3,
    "exercise": 7,
    "period": 14,
}


def _add_alert(
    db: Session,
    user_id: int,
    alert_type: AlertType,
    metric: str,
    message: str,
) -> None:
    """Write an Alert row only if an identical unread alert doesn't already exist."""
    existing = db.scalars(
        select(Alert).where(
            Alert.user_id == user_id,
            Alert.metric == metric,
            Alert.alert_type == alert_type,
            Alert.is_read == False,  # noqa: E712
        )
    ).first()
    if existing:
        return  # avoid duplicate spamming
    db.add(
        Alert(
            user_id=user_id,
            alert_type=alert_type,
            metric=metric,
            message=message,
        )
    )


def _check_stale(db: Session, user_id: int) -> None:
    """Fire stale-data alerts for any metric that hasn't been updated recently."""
    now = _NOW()

    checks: list[tuple[str, datetime | None]] = [
        (
            "basic_indicators",
            db.scalars(
                select(BasicIndicatorRecord.recorded_at)
                .where(BasicIndicatorRecord.user_id == user_id)
                .order_by(BasicIndicatorRecord.recorded_at.desc())
                .limit(1)
            ).first(),
        ),
        (
            "diet",
            db.scalars(
                select(DietRecord.recorded_at)
                .where(DietRecord.user_id == user_id)
                .order_by(DietRecord.recorded_at.desc())
                .limit(1)
            ).first(),
        ),
        (
            "sleep",
            db.scalars(
                select(SleepRecord.sleep_start)
                .where(SleepRecord.user_id == user_id)
                .order_by(SleepRecord.sleep_start.desc())
                .limit(1)
            ).first(),
        ),
        (
            "exercise",
            db.scalars(
                select(ExerciseRecord.recorded_at)
                .where(ExerciseRecord.user_id == user_id)
                .order_by(ExerciseRecord.recorded_at.desc())
                .limit(1)
            ).first(),
        ),
        (
            "period",
            db.scalars(
                select(PeriodRecord.recorded_at)
                .where(PeriodRecord.user_id == user_id)
                .order_by(PeriodRecord.recorded_at.desc())
                .limit(1)
            ).first(),
        ),
    ]

    for metric, last_at in checks:
        threshold_days = _STALE_THRESHOLDS[metric]
        if last_at is None:
            days_old = threshold_days + 1  # never recorded → definitely stale
        else:
            # Ensure both datetimes are timezone-aware for comparison
            if last_at.tzinfo is None:
                last_at = last_at.replace(tzinfo=timezone.utc)
            days_old = (now - last_at).days

        if days_old >= threshold_days:
            _add_alert(
                db,
                user_id,
                AlertType.stale,
                metric,
                f"Your {metric.replace('_', ' ')} has not been updated in {days_old} day(s). "
                f"Please log your data to keep your health profile accurate.",
            )


def _check_abnormal(db: Session, user_id: int) -> None:
    """Check the most recent readings for out-of-range values."""

    # ---- Weight / BMI ---------------------------------------------------- #
    latest_bi = db.scalars(
        select(BasicIndicatorRecord)
        .where(BasicIndicatorRecord.user_id == user_id)
        .order_by(BasicIndicatorRecord.recorded_at.desc())
        .limit(1)
    ).first()

    if latest_bi:
        height_m = latest_bi.height_ft * 0.3048
        weight_kg = latest_bi.weight_lbs * 0.453592
        bmi = weight_kg / (height_m**2) if height_m else 0
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

    # ---- Sleep duration --------------------------------------------------- #
    latest_sleep = db.scalars(
        select(SleepRecord)
        .where(SleepRecord.user_id == user_id)
        .order_by(SleepRecord.sleep_start.desc())
        .limit(1)
    ).first()

    if latest_sleep:
        hours = (latest_sleep.wake_time - latest_sleep.sleep_start).total_seconds() / 3600
        if hours < 5.0:
            _add_alert(
                db,
                user_id,
                AlertType.abnormal,
                "sleep",
                f"You slept only {hours:.1f} hours last night — well below the recommended 7–9 hours.",
            )
        elif hours > 10.0:
            _add_alert(
                db,
                user_id,
                AlertType.abnormal,
                "sleep",
                f"You slept {hours:.1f} hours last night. Consistently sleeping over 10 hours may indicate an underlying issue.",
            )

    # ---- Calorie intake --------------------------------------------------- #
    latest_diet = db.scalars(
        select(DietRecord)
        .where(DietRecord.user_id == user_id)
        .order_by(DietRecord.recorded_at.desc())
        .limit(1)
    ).first()

    if latest_diet:
        if latest_diet.calorie_intake < 1000:
            _add_alert(
                db,
                user_id,
                AlertType.abnormal,
                "calories",
                f"Your logged calorie intake ({latest_diet.calorie_intake:.0f} kcal) is very low. "
                "Severe calorie restriction can be harmful.",
            )
        elif latest_diet.calorie_intake > 5000:
            _add_alert(
                db,
                user_id,
                AlertType.abnormal,
                "calories",
                f"Your logged calorie intake ({latest_diet.calorie_intake:.0f} kcal) is unusually high. "
                "If this is sustained, it may impact your health goals.",
            )


def run_monitor(db: Session, user_id: int) -> list[Alert]:
    """Run all monitor checks for a user and return any newly added alerts."""
    before_ids = set(
        db.scalars(select(Alert.id).where(Alert.user_id == user_id)).all()
    )
    _check_stale(db, user_id)
    _check_abnormal(db, user_id)
    db.commit()
    after_ids = set(
        db.scalars(select(Alert.id).where(Alert.user_id == user_id)).all()
    )
    new_ids = after_ids - before_ids
    return db.scalars(select(Alert).where(Alert.id.in_(new_ids))).all()  # type: ignore[return-value]
