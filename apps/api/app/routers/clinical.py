"""Clinical history and visit report router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
<<<<<<< HEAD
from app.dependencies import get_current_user
from app.models.clinical import ClinicalHistory, ClinicVisitReport
from app.models.user import UserProfile
=======
from app.models.clinical import ClinicalHistory, ClinicVisitReport
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
from app.schemas.clinical import (
    ClinicVisitReportCreate,
    ClinicVisitReportRead,
    ClinicalHistoryCreate,
    ClinicalHistoryRead,
)

router = APIRouter(prefix="/clinical", tags=["clinical"])

<<<<<<< HEAD

@router.get("/history", response_model=ClinicalHistoryRead | None)
def get_clinical_history(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClinicalHistory | None:
    return db.scalars(
        select(ClinicalHistory).where(ClinicalHistory.user_id == current_user.id)
=======
_DEFAULT_USER_ID = 1


@router.get("/history", response_model=ClinicalHistoryRead | None)
def get_clinical_history(db: Session = Depends(get_db)) -> ClinicalHistory | None:
    return db.scalars(
        select(ClinicalHistory).where(ClinicalHistory.user_id == _DEFAULT_USER_ID)
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
    ).first()


@router.put("/history", response_model=ClinicalHistoryRead)
def upsert_clinical_history(
    payload: ClinicalHistoryCreate,
<<<<<<< HEAD
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClinicalHistory:
    record = db.scalars(
        select(ClinicalHistory).where(ClinicalHistory.user_id == current_user.id)
    ).first()
    if record is None:
        record = ClinicalHistory(user_id=current_user.id, **payload.model_dump())
=======
    db: Session = Depends(get_db),
) -> ClinicalHistory:
    record = db.scalars(
        select(ClinicalHistory).where(ClinicalHistory.user_id == _DEFAULT_USER_ID)
    ).first()
    if record is None:
        record = ClinicalHistory(user_id=_DEFAULT_USER_ID, **payload.model_dump())
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
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
<<<<<<< HEAD
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClinicVisitReport:
    report = ClinicVisitReport(user_id=current_user.id, **payload.model_dump())
=======
    db: Session = Depends(get_db),
) -> ClinicVisitReport:
    report = ClinicVisitReport(user_id=_DEFAULT_USER_ID, **payload.model_dump())
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/visits", response_model=list[ClinicVisitReportRead])
def list_visit_reports(
    limit: int = 20,
<<<<<<< HEAD
    current_user: UserProfile = Depends(get_current_user),
=======
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
    db: Session = Depends(get_db),
) -> list[ClinicVisitReport]:
    return db.scalars(  # type: ignore[return-value]
        select(ClinicVisitReport)
<<<<<<< HEAD
        .where(ClinicVisitReport.user_id == current_user.id)
=======
        .where(ClinicVisitReport.user_id == _DEFAULT_USER_ID)
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
        .order_by(ClinicVisitReport.visit_date.desc())
        .limit(limit)
    ).all()
