"""Clinical history and visit report router."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.clinical import ClinicVisitReport
from app.models.medical import ClinicalHistoryEntry
from app.schemas.clinical import (
    ClinicalHistoryCreate,
    ClinicalHistoryRead,
    ClinicVisitReportCreate,
    ClinicVisitReportRead,
)

router = APIRouter(prefix="/clinical", tags=["clinical"])

_DEFAULT_USER_ID = 1


@router.get("/history", response_model=list[ClinicalHistoryRead])
def get_clinical_history(db: Session = Depends(get_db)) -> list[ClinicalHistoryEntry]:
    return db.scalars(
        select(ClinicalHistoryEntry)
        .where(ClinicalHistoryEntry.user_id == _DEFAULT_USER_ID)
        .order_by(
            ClinicalHistoryEntry.diagnosis_date.desc(),
            ClinicalHistoryEntry.start_date.desc(),
            ClinicalHistoryEntry.id.desc(),
        )
    ).all()


@router.post("/history", response_model=ClinicalHistoryRead, status_code=201)
def add_clinical_history(
    payload: ClinicalHistoryCreate,
    db: Session = Depends(get_db),
) -> ClinicalHistoryEntry:
    record = ClinicalHistoryEntry(user_id=_DEFAULT_USER_ID, **payload.model_dump())
    db.add(record)
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
    return db.scalars(
        select(ClinicVisitReport)
        .where(ClinicVisitReport.user_id == _DEFAULT_USER_ID)
        .order_by(ClinicVisitReport.visit_date.desc())
        .limit(limit)
    ).all()
