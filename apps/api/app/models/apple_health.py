"""Apple Health sync record — stores the most recent simulated HealthKit import per user."""

import json
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AppleHealthSync(Base):
    __tablename__ = "apple_health_sync"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_profiles.id"), index=True)
    steps_json: Mapped[str] = mapped_column(Text)   # JSON array of 7 ints
    sleep_json: Mapped[str] = mapped_column(Text)   # JSON array of 7 floats
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    @property
    def steps(self) -> list[int]:
        return json.loads(self.steps_json)

    @property
    def sleep(self) -> list[float]:
        return json.loads(self.sleep_json)
