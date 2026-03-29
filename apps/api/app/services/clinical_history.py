"""Clinical history helpers for onboarding and profile context."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.clinical import ClinicalHistory
from app.schemas.clinical import ClinicalHistoryCreate


def get_clinical_history(db: Session, user_id: int) -> ClinicalHistory | None:
    return db.scalars(
        select(ClinicalHistory).where(ClinicalHistory.user_id == user_id).limit(1)
    ).first()


def upsert_clinical_history(
    db: Session,
    user_id: int,
    payload: ClinicalHistoryCreate,
) -> ClinicalHistory:
    history = get_clinical_history(db, user_id)
    values = payload.model_dump()

    if history is None:
        history = ClinicalHistory(user_id=user_id, **values)
        db.add(history)
    else:
        history.injuries = values["injuries"]
        history.surgeries = values["surgeries"]
        history.constraints = values["constraints"]

    db.commit()
    db.refresh(history)
    return history
