"""Stats router — returns computed statistics for the dashboard and LLM context."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.analysis_service import get_dashboard_stats

router = APIRouter(prefix="/stats", tags=["stats"])

_DEFAULT_USER_ID = 1


@router.get("")
def get_stats(db: Session = Depends(get_db)) -> dict:
    """Return dashboard statistics for the current user."""
    return get_dashboard_stats(_DEFAULT_USER_ID, db)
