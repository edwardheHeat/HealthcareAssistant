"""Analysis orchestrator — called after any new health record is saved.

Runs the monitor and returns new alerts so the router can include them in
the API response, giving the frontend immediate feedback.
"""

from sqlalchemy.orm import Session

from app.models.alerts import Alert
from app.services.analysis_generation import refresh_dashboard_analysis
from app.services.monitor import run_monitor


def analyze_after_submission(db: Session, user_id: int) -> list[Alert]:
    """Run health monitor checks and refresh stored dashboard analysis."""
    alerts = run_monitor(db, user_id)
    refresh_dashboard_analysis(db, user_id)
    return alerts
