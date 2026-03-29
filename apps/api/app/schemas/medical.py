from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ClinicalHistoryCreate(BaseModel):
    user_id: int = Field(default=1, ge=1)
    illness_name: str = Field(..., max_length=120)
    diagnosis_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    medication: str | None = None

    @model_validator(mode="after")
    def validate_date_range(self) -> "ClinicalHistoryCreate":
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date must be on or after start_date")
        return self


class ClinicalHistoryRead(ClinicalHistoryCreate):
    id: int

    model_config = {"from_attributes": True}


class VaccineRecordCreate(BaseModel):
    user_id: int = Field(default=1, ge=1)
    vaccine_name: str = Field(..., max_length=120)
    date_administered: date


class VaccineRecordRead(VaccineRecordCreate):
    id: int

    model_config = {"from_attributes": True}


class HealthAlertCreate(BaseModel):
    user_id: int = Field(default=1, ge=1)
    date: date
    alert_type: str = Field(..., max_length=80)
    severity: Literal["low", "medium", "high"]
    description: str = Field(..., min_length=1)


class HealthAlertRead(HealthAlertCreate):
    id: int

    model_config = {"from_attributes": True}
