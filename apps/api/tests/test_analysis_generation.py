import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.db import Base
from app.models.analysis import IndicatorAnalysis, OverallAnalysis
from app.models.daily_tracking import (
    DailyBasicMetrics,
    DailyDiet,
    DailyExercise,
    DailySleep,
)
from app.models.user import UserProfile
from app.services.analysis import analyze_after_submission
from app.services.analysis_generation import refresh_dashboard_analysis


def _build_fake_client(content: str) -> SimpleNamespace:
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    completions = SimpleNamespace(create=lambda **_: SimpleNamespace(choices=[choice]))
    chat = SimpleNamespace(completions=completions)
    return SimpleNamespace(chat=chat)


def test_refresh_dashboard_analysis_persists_generated_rows(monkeypatch) -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    payload = {
        "basic": {
            "7d": "Weight stayed fairly stable this week.",
            "30d": "Weight is up slightly over the month.",
        },
        "diet": {
            "7d": "Calories were consistent this week.",
            "30d": "Diet intake stayed close to baseline.",
        },
        "exercise": {
            "7d": "Activity picked up over the last week.",
            "30d": "Exercise volume remained moderate this month.",
        },
        "sleep": {
            "7d": "Sleep duration was slightly below target.",
            "30d": "Sleep quality remained steady overall.",
        },
        "overall_summary": (
            "Recent health trends look fairly stable "
            "with a few areas to keep watching."
        ),
    }
    monkeypatch.setattr(
        "app.services.analysis_generation.get_sync_llm_client",
        lambda: _build_fake_client(json.dumps(payload)),
    )

    with TestingSession() as db:
        user = UserProfile(
            name="Test User",
            account_id="test-user",
            password_hash="hashed",
            age=35,
            sex="F",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        now = datetime.now(tz=UTC)
        db.add(
            DailyBasicMetrics(
                user_id=user.id,
                date=now.date(),
                height_cm=165.0,
                weight_kg=68.0,
            )
        )
        db.add(
            DailyDiet(
                user_id=user.id,
                date=now.date(),
                breakfast_calories=300,
                lunch_calories=450,
                dinner_calories=550,
                protein_g=90.0,
                carbs_g=120.0,
                fat_g=40.0,
            )
        )
        db.add(
            DailyExercise(
                user_id=user.id,
                date=now.date(),
                duration_minutes=45,
                intensity="medium",
            )
        )
        db.add(
            DailySleep(
                user_id=user.id,
                date=now.date(),
                sleep_start=now - timedelta(hours=8),
                sleep_end=now,
                quality=4,
            )
        )
        db.commit()

        refresh_dashboard_analysis(db, user.id)

        indicator_rows = db.scalars(
            select(IndicatorAnalysis).order_by(
                IndicatorAnalysis.category,
                IndicatorAnalysis.period_type,
            )
        ).all()
        overall_rows = db.scalars(select(OverallAnalysis)).all()

    assert len(indicator_rows) == 8
    assert len(overall_rows) == 1
    assert indicator_rows[0].analysis_text
    assert overall_rows[0].summary_text == payload["overall_summary"]


def test_analyze_after_submission_runs_monitor_and_refresh(monkeypatch) -> None:
    expected_alerts = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
    calls: list[str] = []

    def fake_run_monitor(db, user_id):
        calls.append(f"monitor:{user_id}")
        return expected_alerts

    def fake_refresh_dashboard_analysis(db, user_id):
        calls.append(f"refresh:{user_id}")

    monkeypatch.setattr("app.services.analysis.run_monitor", fake_run_monitor)
    monkeypatch.setattr(
        "app.services.analysis.refresh_dashboard_analysis",
        fake_refresh_dashboard_analysis,
    )

    alerts = analyze_after_submission(db=SimpleNamespace(), user_id=1)

    assert alerts == expected_alerts
    assert calls == ["monitor:1", "refresh:1"]
