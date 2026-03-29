from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

from sqlalchemy import create_engine
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
from app.models.reproductive import PeriodCycle
from app.models.user import UserProfile
from app.services.analysis_service import (
    _compute_period_cycle_from_logs,
    compute_basic_stats,
    compute_diet_stats,
    compute_exercise_stats,
    compute_sleep_stats,
    get_dashboard_stats,
    get_latest_indicator_analysis,
    get_latest_overall_analysis,
)


def _days_ago(days: int) -> date:
    return datetime.now(tz=UTC).date() - timedelta(days=days)


def test_compute_basic_stats_handles_missing_days_and_trend() -> None:
    logs = [
        SimpleNamespace(date=_days_ago(35), weight_kg=70.0),
        SimpleNamespace(date=_days_ago(25), weight_kg=72.0),
        SimpleNamespace(date=_days_ago(3), weight_kg=75.0),
        SimpleNamespace(date=_days_ago(1), weight_kg=74.0),
    ]

    stats = compute_basic_stats(logs)

    assert stats["avg_weight_7d"] == 74.5
    assert stats["avg_weight_30d"] == 73.67
    assert stats["previous_avg_weight_30d"] == 70.0
    assert stats["weight_trend"] == 3.67
    assert len(stats["bar_chart_data"]["last_7_days"]) == 7
    assert any(
        point["value"] is None for point in stats["bar_chart_data"]["last_7_days"]
    )


def test_compute_diet_stats_returns_calorie_and_macro_averages() -> None:
    logs = [
        SimpleNamespace(
            date=_days_ago(10),
            breakfast_calories=300,
            lunch_calories=400,
            dinner_calories=500,
            protein_g=80.0,
            carbs_g=120.0,
            fat_g=40.0,
        ),
        SimpleNamespace(
            date=_days_ago(2),
            breakfast_calories=350,
            lunch_calories=450,
            dinner_calories=550,
            protein_g=90.0,
            carbs_g=130.0,
            fat_g=50.0,
        ),
    ]

    stats = compute_diet_stats(logs)

    assert stats["avg_calories_7d"] == 1350.0
    assert stats["avg_calories_30d"] == 1275.0
    assert stats["avg_protein_g_30d"] == 85.0
    assert stats["avg_carbs_g_30d"] == 125.0
    assert stats["avg_fat_g_30d"] == 45.0
    assert len(stats["bar_chart_data"]["last_30_days"]) == 30


def test_compute_exercise_stats_returns_distribution() -> None:
    logs = [
        SimpleNamespace(date=_days_ago(20), duration_minutes=30, intensity="low"),
        SimpleNamespace(date=_days_ago(5), duration_minutes=45, intensity="medium"),
        SimpleNamespace(date=_days_ago(1), duration_minutes=60, intensity="high"),
    ]

    stats = compute_exercise_stats(logs)

    assert stats["avg_duration_7d"] == 52.5
    assert stats["avg_duration_30d"] == 45.0
    assert stats["intensity_distribution"] == {"low": 1, "medium": 1, "high": 1}


def test_compute_sleep_stats_returns_duration_and_quality() -> None:
    logs = [
        SimpleNamespace(
            date=_days_ago(8),
            sleep_start=datetime.now(tz=UTC) - timedelta(days=8, hours=8),
            sleep_end=datetime.now(tz=UTC) - timedelta(days=8),
            quality=3,
        ),
        SimpleNamespace(
            date=_days_ago(1),
            sleep_start=datetime.now(tz=UTC) - timedelta(days=1, hours=7, minutes=30),
            sleep_end=datetime.now(tz=UTC) - timedelta(days=1),
            quality=5,
        ),
    ]

    stats = compute_sleep_stats(logs)

    assert stats["avg_sleep_duration_7d"] == 7.5
    assert stats["avg_sleep_duration_30d"] == 7.75
    assert stats["avg_quality_30d"] == 4.0
    assert len(stats["bar_chart_data"]["last_7_days"]) == 7


def test_compute_period_cycle_predicts_next_window() -> None:
    logs = [
        SimpleNamespace(
            start_date=_days_ago(90),
            end_date=_days_ago(85),
        ),
        SimpleNamespace(
            start_date=_days_ago(60),
            end_date=_days_ago(55),
        ),
        SimpleNamespace(
            start_date=_days_ago(30),
            end_date=_days_ago(25),
        ),
    ]

    stats = _compute_period_cycle_from_logs(logs)

    assert stats["avg_cycle_length_days"] == 30.0
    assert stats["predicted_next_start_start"] is not None
    assert stats["predicted_next_start_end"] is not None


def test_get_dashboard_stats_queries_database() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

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

        db.add(
            DailyBasicMetrics(
                user_id=user.id,
                date=_days_ago(1),
                height_cm=165.0,
                weight_kg=68.0,
            )
        )
        db.add(
            DailyDiet(
                user_id=user.id,
                date=_days_ago(1),
                breakfast_calories=300,
                lunch_calories=450,
                dinner_calories=550,
                protein_g=85.0,
                carbs_g=130.0,
                fat_g=45.0,
            )
        )
        db.add(
            DailyExercise(
                user_id=user.id,
                date=_days_ago(1),
                duration_minutes=40,
                intensity="medium",
            )
        )
        db.add(
            DailySleep(
                user_id=user.id,
                date=_days_ago(1),
                sleep_start=datetime.now(tz=UTC) - timedelta(days=1, hours=8),
                sleep_end=datetime.now(tz=UTC) - timedelta(days=1),
                quality=4,
            )
        )
        db.add(
            PeriodCycle(
                user_id=user.id,
                start_date=_days_ago(28),
                end_date=_days_ago(24),
            )
        )
        db.add_all(
            [
                IndicatorAnalysis(
                    user_id=user.id,
                    category="basic",
                    period_type="7d",
                    analysis_text="Older 7d basic summary",
                    created_at=datetime.now(tz=UTC) - timedelta(days=2),
                ),
                IndicatorAnalysis(
                    user_id=user.id,
                    category="basic",
                    period_type="7d",
                    analysis_text="Latest 7d basic summary",
                    created_at=datetime.now(tz=UTC) - timedelta(hours=1),
                ),
                IndicatorAnalysis(
                    user_id=user.id,
                    category="diet",
                    period_type="30d",
                    analysis_text="Latest 30d diet summary",
                    created_at=datetime.now(tz=UTC) - timedelta(minutes=30),
                ),
                OverallAnalysis(
                    user_id=user.id,
                    summary_text="Older overall summary",
                    created_at=datetime.now(tz=UTC) - timedelta(days=1),
                ),
                OverallAnalysis(
                    user_id=user.id,
                    summary_text="Latest overall summary",
                    created_at=datetime.now(tz=UTC),
                ),
            ]
        )
        db.commit()

        indicator_analysis = get_latest_indicator_analysis(user.id, db)
        overall_analysis = get_latest_overall_analysis(user.id, db)
        stats = get_dashboard_stats(user.id, db)

    assert indicator_analysis["basic"]["7d"] == "Latest 7d basic summary"
    assert indicator_analysis["basic"]["30d"] is None
    assert indicator_analysis["diet"]["30d"] == "Latest 30d diet summary"
    assert overall_analysis is not None
    assert overall_analysis["summary"] == "Latest overall summary"

    assert set(stats.keys()) == {"stats", "analysis", "overall_analysis"}
    assert set(stats["stats"].keys()) == {
        "basic",
        "diet",
        "exercise",
        "sleep",
        "period_cycle",
    }
    assert stats["stats"]["basic"]["avg_weight_7d"] == 68.0
    assert stats["stats"]["diet"]["avg_calories_7d"] == 1300.0
    assert stats["stats"]["exercise"]["avg_duration_7d"] == 40.0
    assert stats["stats"]["sleep"]["avg_quality_7d"] == 4.0
    assert stats["analysis"]["basic"]["7d"] == "Latest 7d basic summary"
    assert stats["analysis"]["exercise"]["7d"] is None
    assert stats["overall_analysis"] is not None
    assert stats["overall_analysis"]["summary"] == "Latest overall summary"
