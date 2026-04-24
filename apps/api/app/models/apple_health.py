"""Apple Health data models — mock 7-day sync (legacy) and full XML export (rich)."""

import json
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AppleHealthSync(Base):
    """Legacy: stores a 7-element mock step/sleep array per user."""

    __tablename__ = "apple_health_sync"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_profiles.id"), index=True)
    steps_json: Mapped[str] = mapped_column(Text)
    sleep_json: Mapped[str] = mapped_column(Text)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    @property
    def steps(self) -> list[int]:
        return json.loads(self.steps_json)

    @property
    def sleep(self) -> list[float]:
        return json.loads(self.sleep_json)


class AppleHealthExport(Base):
    """Parsed Apple Health XML export — stores 30-day aggregated daily data."""

    __tablename__ = "apple_health_export"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_profiles.id"), index=True)
    parsed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # JSON-serialised dicts: {date_str -> value}
    daily_steps_json: Mapped[str] = mapped_column(Text)
    daily_workouts_json: Mapped[str] = mapped_column(Text)
    daily_active_energy_json: Mapped[str] = mapped_column(Text)
    daily_sleep_json: Mapped[str] = mapped_column(Text)
    totals_json: Mapped[str] = mapped_column(Text)

    @property
    def daily_steps(self) -> dict[str, int]:
        return json.loads(self.daily_steps_json)

    @property
    def daily_workouts(self) -> dict[str, list]:
        return json.loads(self.daily_workouts_json)

    @property
    def daily_active_energy(self) -> dict[str, float]:
        return json.loads(self.daily_active_energy_json)

    @property
    def daily_sleep(self) -> dict[str, float]:
        return json.loads(self.daily_sleep_json)

    @property
    def totals(self) -> dict:
        return json.loads(self.totals_json)
