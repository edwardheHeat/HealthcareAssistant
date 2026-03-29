"""Tests for trigger_monitor() — the monitor entry point.

These test the wiring (dispatch → findings → LLM → Alert written) with
the LLM mocked so no real API calls are made.

Run:
    cd apps/api
    LLM_BASE_URL=x LLM_API_KEY=x LLM_MODEL=x pytest tests/test_monitor_service.py -v
"""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 — register all tables
from app.db import Base
from app.llm.alert_writer import AbnormalFinding
from app.models.alerts import Alert, AlertSeverity, AlertType
from app.models.user import UserProfile
from app.services.monitor import trigger_monitor, _CHECKS
from app.services.monitor_types import SleepSnapshot, BasicIndicatorSnapshot


# ---------------------------------------------------------------------------
# In-memory SQLite DB fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def db() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # Seed a user so trigger_monitor can look up the profile
    user = UserProfile(
        name="Test User",
        account_id="test01",
        password_hash="hashed",
        age=35,
        sex="F",
    )
    session.add(user)
    session.commit()

    yield session
    session.close()


_FAKE_FINDING = AbnormalFinding(
    metric="sleep",
    severity="critical",
    evaluation_mode="immediate",
    raw_description="sleep=4.5hrs, threshold=5hrs",
)

_FAKE_ALERT_MSG = "You slept only 4.5 hours last night. Consider going to bed earlier."


# ---------------------------------------------------------------------------
# Tests for the dispatch table
# ---------------------------------------------------------------------------

class TestDispatchTable:
    def test_all_metrics_have_checks(self) -> None:
        expected = {"basic_indicators", "diet", "sleep", "exercise", "period"}
        assert set(_CHECKS.keys()) == expected

    def test_each_metric_has_at_least_one_check(self) -> None:
        for metric, fns in _CHECKS.items():
            assert len(fns) >= 1, f"{metric} has no check functions"


# ---------------------------------------------------------------------------
# trigger_monitor — no findings → no alert written
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_trigger_monitor_no_findings_returns_none(db: Session) -> None:
    snap = SleepSnapshot(current_duration_hrs=7.5, trend_stats={})

    # All check functions return None (stubs) → no alert written
    result = await trigger_monitor(db, user_id=1, snapshot=snap)
    assert result is None

    alerts = db.scalars(select(Alert)).all()
    assert len(alerts) == 0


# ---------------------------------------------------------------------------
# trigger_monitor — finding found → LLM called, Alert written
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_trigger_monitor_with_finding_writes_alert(db: Session) -> None:
    snap = SleepSnapshot(current_duration_hrs=4.0, trend_stats={})

    # Patch check_sleep_duration to return a real finding
    # and patch generate_alert_message to avoid a real LLM call
    with (
        patch(
            "app.services.monitor.check_sleep_duration",
            return_value=_FAKE_FINDING,
        ),
        patch(
            "app.services.monitor.generate_alert_message",
            new=AsyncMock(return_value=_FAKE_ALERT_MSG),
        ),
    ):
        result = await trigger_monitor(db, user_id=1, snapshot=snap)

    assert result is not None
    assert isinstance(result, Alert)
    assert result.alert_type == AlertType.abnormal
    assert result.metric == "sleep"
    assert result.message == _FAKE_ALERT_MSG
    assert result.is_read is False


# ---------------------------------------------------------------------------
# trigger_monitor — severity escalation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_trigger_monitor_critical_finding_escalates_severity(db: Session) -> None:
    snap = SleepSnapshot(current_duration_hrs=3.0, trend_stats={})

    critical_finding = AbnormalFinding(
        metric="sleep",
        severity="critical",
        evaluation_mode="immediate",
        raw_description="sleep=3.0hrs",
    )

    with (
        patch("app.services.monitor.check_sleep_duration", return_value=critical_finding),
        patch("app.services.monitor.generate_alert_message", new=AsyncMock(return_value="Critical alert.")),
    ):
        result = await trigger_monitor(db, user_id=1, snapshot=snap)

    assert result is not None
    assert result.severity == AlertSeverity.critical


@pytest.mark.asyncio
async def test_trigger_monitor_warning_finding_sets_warning_severity(db: Session) -> None:
    # 11.0 hours naturally triggers a warning finding
    snap = SleepSnapshot(current_duration_hrs=11.0, trend_stats={})

    with patch("app.services.monitor.generate_alert_message", new=AsyncMock(return_value="Warning alert.")):
        result = await trigger_monitor(db, user_id=1, snapshot=snap)

    assert result is not None
    assert result.severity == AlertSeverity.warning


# ---------------------------------------------------------------------------
# trigger_monitor — multiple findings escalated to critical
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_trigger_monitor_mixed_findings_escalate_to_critical(db: Session) -> None:
    snap = BasicIndicatorSnapshot(
        current_height_cm=170.0,
        current_weight_kg=130.0,
        previous_weight_kg=120.0,
        trend_stats={},
    )

    warning_finding = AbnormalFinding("basic_indicators", "warning", "immediate", "BMI=40")
    critical_finding = AbnormalFinding("basic_indicators", "critical", "trend", "+20lbs gain")

    with (
        patch("app.services.monitor.check_bmi", return_value=warning_finding),
        patch("app.services.monitor.check_weight_change", return_value=critical_finding),
        patch("app.services.monitor.generate_alert_message", new=AsyncMock(return_value="Escalated.")),
    ):
        result = await trigger_monitor(db, user_id=1, snapshot=snap)

    assert result is not None
    assert result.severity == AlertSeverity.critical


# ---------------------------------------------------------------------------
# trigger_monitor — unknown user returns None
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_trigger_monitor_unknown_user_returns_none(db: Session) -> None:
    snap = SleepSnapshot(current_duration_hrs=4.0, trend_stats={})

    with patch("app.services.monitor.check_sleep_duration", return_value=_FAKE_FINDING):
        result = await trigger_monitor(db, user_id=999, snapshot=snap)

    assert result is None
    alerts = db.scalars(select(Alert)).all()
    assert len(alerts) == 0
