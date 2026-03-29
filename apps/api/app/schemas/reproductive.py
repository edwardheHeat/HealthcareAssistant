from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator


class PeriodCycleCreate(BaseModel):
    user_id: int = Field(default=1, ge=1)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_date_range(self) -> "PeriodCycleCreate":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class PeriodCycleRead(PeriodCycleCreate):
    id: int

    model_config = {"from_attributes": True}


class PeriodCycleSummaryCreate(BaseModel):
    user_id: int = Field(default=1, ge=1)
    avg_cycle_length_days: float = Field(..., gt=0)
    predicted_next_start_start: date
    predicted_next_start_end: date
    analysis_text: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_prediction_window(self) -> "PeriodCycleSummaryCreate":
        if self.predicted_next_start_end < self.predicted_next_start_start:
            raise ValueError(
                "predicted_next_start_end must be on or after "
                "predicted_next_start_start"
            )
        return self


class PeriodCycleSummaryRead(PeriodCycleSummaryCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
