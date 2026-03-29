"""Alerts router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
<<<<<<< HEAD
from app.dependencies import get_current_user
from app.models.alerts import Alert
from app.models.user import UserProfile
=======
from app.models.alerts import Alert
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
from app.schemas.alerts import AlertRead

router = APIRouter(prefix="/alerts", tags=["alerts"])

<<<<<<< HEAD
=======
_DEFAULT_USER_ID = 1

>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156

@router.get("", response_model=list[AlertRead])
def list_alerts(
    unread_only: bool = False,
    limit: int = 50,
<<<<<<< HEAD
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Alert]:
    q = select(Alert).where(Alert.user_id == current_user.id)
=======
    db: Session = Depends(get_db),
) -> list[Alert]:
    q = select(Alert).where(Alert.user_id == _DEFAULT_USER_ID)
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
    if unread_only:
        q = q.where(Alert.is_read == False)  # noqa: E712
    q = q.order_by(Alert.created_at.desc()).limit(limit)
    return db.scalars(q).all()  # type: ignore[return-value]


@router.patch("/{alert_id}/read", response_model=AlertRead)
<<<<<<< HEAD
def mark_alert_read(
    alert_id: int,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Alert:
    alert = db.get(Alert, alert_id)
    if alert is None or alert.user_id != current_user.id:
=======
def mark_alert_read(alert_id: int, db: Session = Depends(get_db)) -> Alert:
    alert = db.get(Alert, alert_id)
    if alert is None or alert.user_id != _DEFAULT_USER_ID:
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
        raise HTTPException(status_code=404, detail="Alert not found.")
    alert.is_read = True
    db.commit()
    db.refresh(alert)
    return alert
