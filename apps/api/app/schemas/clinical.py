from datetime import date, datetime

from pydantic import BaseModel


class ClinicalHistoryCreate(BaseModel):
    injuries: str | None = None
    surgeries: str | None = None
    constraints: str | None = None


class ClinicalHistoryRead(ClinicalHistoryCreate):
    id: int
    user_id: int
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClinicVisitReportCreate(BaseModel):
    visit_date: date
    summary: str
    raw_notes: str | None = None


class ClinicVisitReportRead(ClinicVisitReportCreate):
    id: int
    user_id: int

    model_config = {"from_attributes": True}
