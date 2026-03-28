"""Clinical history and visit report router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.clinical import ClinicalHistory, ClinicVisitReport
from app.schemas.clinical import (
    ClinicVisitReportCreate,
    ClinicVisitReportRead,
    ClinicalHistoryCreate,
    ClinicalHistoryRead,
)

router = APIRouter(prefix="/clinical", tags=["clinical"])

_DEFAULT_USER_ID = 1


@router.get("/history", response_model=ClinicalHistoryRead | None)
def get_clinical_history(db: Session = Depends(get_db)) -> ClinicalHistory | None:
    return db.scalars(
        select(ClinicalHistory).where(ClinicalHistory.user_id == _DEFAULT_USER_ID)
    ).first()


@router.put("/history", response_model=ClinicalHistoryRead)
def upsert_clinical_history(
    payload: ClinicalHistoryCreate,
    db: Session = Depends(get_db),
) -> ClinicalHistory:
    record = db.scalars(
        select(ClinicalHistory).where(ClinicalHistory.user_id == _DEFAULT_USER_ID)
    ).first()
    if record is None:
        record = ClinicalHistory(user_id=_DEFAULT_USER_ID, **payload.model_dump())
        db.add(record)
    else:
        for field, value in payload.model_dump().items():
            setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record


@router.post("/visits", response_model=ClinicVisitReportRead, status_code=201)
def add_visit_report(
    payload: ClinicVisitReportCreate,
    db: Session = Depends(get_db),
) -> ClinicVisitReport:
    report = ClinicVisitReport(user_id=_DEFAULT_USER_ID, **payload.model_dump())
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/visits", response_model=list[ClinicVisitReportRead])
def list_visit_reports(
    limit: int = 20,
    db: Session = Depends(get_db),
) -> list[ClinicVisitReport]:
    return db.scalars(  # type: ignore[return-value]
        select(ClinicVisitReport)
        .where(ClinicVisitReport.user_id == _DEFAULT_USER_ID)
        .order_by(ClinicVisitReport.visit_date.desc())
        .limit(limit)
    ).all()
