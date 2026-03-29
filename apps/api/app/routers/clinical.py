"""Clinical history and visit report router."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models.clinical import ClinicalHistory, ClinicVisitReport
from app.models.user import UserProfile
from app.schemas.clinical import (
    ClinicalHistoryCreate,
    ClinicalHistoryRead,
    ClinicVisitReportCreate,
    ClinicVisitReportRead,
)
from app.services.clinical_history import (
    get_clinical_history as load_clinical_history,
)
from app.services.clinical_history import (
    upsert_clinical_history,
)

router = APIRouter(prefix="/clinical", tags=["clinical"])


@router.get("/history", response_model=ClinicalHistoryRead | None)
def get_clinical_history(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClinicalHistory | None:
    return load_clinical_history(db, current_user.id)


@router.put("/history", response_model=ClinicalHistoryRead)
def save_clinical_history(
    payload: ClinicalHistoryCreate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClinicalHistory:
    return upsert_clinical_history(db, current_user.id, payload)


@router.post("/visits", response_model=ClinicVisitReportRead, status_code=201)
def add_visit_report(
    payload: ClinicVisitReportCreate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClinicVisitReport:
    report = ClinicVisitReport(user_id=current_user.id, **payload.model_dump())
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/visits", response_model=list[ClinicVisitReportRead])
def list_visit_reports(
    limit: int = 20,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ClinicVisitReport]:
    return db.scalars(
        select(ClinicVisitReport)
        .where(ClinicVisitReport.user_id == current_user.id)
        .order_by(ClinicVisitReport.visit_date.desc())
        .limit(limit)
    ).all()
