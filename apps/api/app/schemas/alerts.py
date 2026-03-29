from datetime import datetime

from pydantic import BaseModel

from app.models.alerts import AlertSeverity, AlertType


class AlertRead(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    alert_type: AlertType
    severity: AlertSeverity
    metric: str
    message: str
    is_read: bool

    model_config = {"from_attributes": True}
