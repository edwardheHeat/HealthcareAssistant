from datetime import date

from pydantic import BaseModel

from app.schemas.medical import (
    ClinicalHistoryCreate as ClinicalHistoryCreate,
)
from app.schemas.medical import (
    ClinicalHistoryRead as ClinicalHistoryRead,
)


class ClinicVisitReportCreate(BaseModel):
    visit_date: date
    summary: str
    raw_notes: str | None = None


class ClinicVisitReportRead(ClinicVisitReportCreate):
    id: int
    user_id: int

    model_config = {"from_attributes": True}
