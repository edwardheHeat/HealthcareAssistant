"""Tests for the Alerts API endpoints — including new DELETE endpoints.

Run:
    cd apps/api
    LLM_BASE_URL=x LLM_API_KEY=x LLM_MODEL=x pytest tests/test_alerts_api.py -v
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.db import Base, get_db
from app.main import app
from app.models.alerts import Alert, AlertSeverity, AlertType
from app.models.user import UserProfile


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    db = TestSession()

    # Seed user
    db.add(UserProfile(name="Test", account_id="t1", password_hash="x", age=30, sex="F"))
    db.commit()

    yield TestClient(app), db

    app.dependency_overrides.clear()
    db.close()


def _add_alert(db, metric: str = "sleep", severity: AlertSeverity = AlertSeverity.warning,
               days_ago: int = 0, is_read: bool = False) -> Alert:
    created = datetime.now(tz=timezone.utc) - timedelta(days=days_ago)
    alert = Alert(
        user_id=1,
        alert_type=AlertType.abnormal,
        severity=severity,
        metric=metric,
        message=f"Test alert for {metric}",
        is_read=is_read,
        created_at=created,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


# ---------------------------------------------------------------------------
# GET /alerts — response shape
# ---------------------------------------------------------------------------

class TestGetAlerts:
    def test_returns_empty_list_when_no_alerts(self, client) -> None:
        c, _ = client
        resp = c.get("/api/v1/alerts")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_response_includes_severity_field(self, client) -> None:
        c, db = client
        _add_alert(db, severity=AlertSeverity.critical)
        resp = c.get("/api/v1/alerts")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["severity"] == "critical"

    def test_unread_only_filter(self, client) -> None:
        c, db = client
        _add_alert(db, metric="sleep", is_read=False)
        _add_alert(db, metric="diet", is_read=True)
        resp = c.get("/api/v1/alerts?unread_only=true")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["metric"] == "sleep"

    def test_all_alerts_returned_without_filter(self, client) -> None:
        c, db = client
        _add_alert(db, is_read=False)
        _add_alert(db, is_read=True)
        resp = c.get("/api/v1/alerts")
        assert len(resp.json()) == 2


# ---------------------------------------------------------------------------
# PATCH /alerts/{id}/read
# ---------------------------------------------------------------------------

class TestMarkAlertRead:
    def test_marks_alert_as_read(self, client) -> None:
        c, db = client
        alert = _add_alert(db)
        assert alert.is_read is False
        resp = c.patch(f"/api/v1/alerts/{alert.id}/read")
        assert resp.status_code == 200
        assert resp.json()["is_read"] is True

    def test_unknown_id_returns_404(self, client) -> None:
        c, _ = client
        resp = c.patch("/api/v1/alerts/9999/read")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /alerts/{id} — single
# ---------------------------------------------------------------------------

class TestDeleteSingleAlert:
    def test_deletes_existing_alert(self, client) -> None:
        c, db = client
        alert = _add_alert(db)
        resp = c.delete(f"/api/v1/alerts/{alert.id}")
        assert resp.status_code == 204
        # Confirm absent from list
        assert c.get("/api/v1/alerts").json() == []

    def test_unknown_id_returns_404(self, client) -> None:
        c, _ = client
        resp = c.delete("/api/v1/alerts/9999")
        assert resp.status_code == 404

    def test_does_not_delete_other_alerts(self, client) -> None:
        c, db = client
        a1 = _add_alert(db, metric="sleep")
        a2 = _add_alert(db, metric="diet")
        c.delete(f"/api/v1/alerts/{a1.id}")
        remaining = c.get("/api/v1/alerts").json()
        assert len(remaining) == 1
        assert remaining[0]["metric"] == "diet"


# ---------------------------------------------------------------------------
# DELETE /alerts — bulk
# ---------------------------------------------------------------------------

class TestBulkDeleteAlerts:
    def test_delete_all_alerts(self, client) -> None:
        c, db = client
        _add_alert(db)
        _add_alert(db)
        resp = c.delete("/api/v1/alerts")
        assert resp.status_code == 204
        assert c.get("/api/v1/alerts").json() == []

    def test_delete_all_returns_204_when_empty(self, client) -> None:
        c, _ = client
        resp = c.delete("/api/v1/alerts")
        assert resp.status_code == 204

    def test_delete_by_day_window(self, client) -> None:
        c, db = client
        today_alert = _add_alert(db, metric="sleep", days_ago=0)
        _add_alert(db, metric="diet", days_ago=3)

        # Delete only alerts from the last 24 hours
        now = datetime.now(tz=timezone.utc)
        after = (now - timedelta(hours=23)).isoformat().replace("+00:00", "Z")
        before = (now + timedelta(hours=1)).isoformat().replace("+00:00", "Z")

        resp = c.delete(f"/api/v1/alerts?after_date={after}&before_date={before}")
        assert resp.status_code == 204

        remaining = c.get("/api/v1/alerts").json()
        assert len(remaining) == 1
        assert remaining[0]["metric"] == "diet"

    def test_delete_with_only_before_date(self, client) -> None:
        c, db = client
        _add_alert(db, metric="old", days_ago=5)
        _add_alert(db, metric="new", days_ago=0)

        cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=1)).isoformat().replace("+00:00", "Z")
        c.delete(f"/api/v1/alerts?before_date={cutoff}")

        remaining = c.get("/api/v1/alerts").json()
        assert len(remaining) == 1
        assert remaining[0]["metric"] == "new"
