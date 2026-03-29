from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class IndicatorAnalysisCreate(BaseModel):
    user_id: int = Field(default=1, ge=1)
    category: Literal["basic", "diet", "exercise", "sleep"]
    period_type: Literal["7d", "30d"]
    analysis_text: str = Field(..., min_length=1)


class IndicatorAnalysisRead(IndicatorAnalysisCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class OverallAnalysisCreate(BaseModel):
    user_id: int = Field(default=1, ge=1)
    summary_text: str = Field(..., min_length=1)


class OverallAnalysisRead(OverallAnalysisCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
