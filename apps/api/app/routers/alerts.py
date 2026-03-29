"""Alerts router — read, delete (single + bulk), and mark-read."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models.alerts import Alert
from app.models.user import UserProfile
from app.schemas.alerts import AlertRead

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertRead])
def list_alerts(
    unread_only: bool = False,
    limit: int = 50,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Alert]:
    q = select(Alert).where(Alert.user_id == current_user.id)
    if unread_only:
        q = q.where(Alert.is_read == False)  # noqa: E712
    q = q.order_by(Alert.created_at.desc()).limit(limit)
    return db.scalars(q).all()  # type: ignore[return-value]


@router.patch("/{alert_id}/read", response_model=AlertRead)
def mark_alert_read(
    alert_id: int,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Alert:
    alert = db.get(Alert, alert_id)
    if alert is None or alert.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Alert not found.")
    alert.is_read = True
    db.commit()
    db.refresh(alert)
    return alert


@router.delete("/{alert_id}", status_code=204)
def delete_alert(
    alert_id: int,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Hard-delete a single alert."""
    alert = db.get(Alert, alert_id)
    if alert is None or alert.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Alert not found.")
    db.delete(alert)
    db.commit()


@router.delete("", status_code=204)
def bulk_delete_alerts(
    after_date: datetime | None = Query(
        None,
        description="Delete alerts created at or after this datetime (ISO 8601, UTC).",
    ),
    before_date: datetime | None = Query(
        None,
        description=(
            "Delete alerts created strictly before this datetime "
            "(ISO 8601, UTC)."
        ),
    ),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Bulk-delete alerts.

    - No params → delete ALL alerts for the user.
    - `after_date` and/or `before_date` → delete within that date window.
      Useful for 'Delete Day' (pass the day's start as after_date and
      the next day's start as before_date).
    """
    q = delete(Alert).where(Alert.user_id == current_user.id)
    if after_date is not None:
        if after_date.tzinfo is None:
            after_date = after_date.replace(tzinfo=UTC)
        q = q.where(Alert.created_at >= after_date)
    if before_date is not None:
        if before_date.tzinfo is None:
            before_date = before_date.replace(tzinfo=UTC)
        q = q.where(Alert.created_at < before_date)
    db.execute(q)
    db.commit()
