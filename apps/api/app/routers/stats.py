"""Stats router — returns computed statistics for the dashboard and LLM context."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.stats import build_user_stats_context

router = APIRouter(prefix="/stats", tags=["stats"])

_DEFAULT_USER_ID = 1


@router.get("")
def get_stats(db: Session = Depends(get_db)) -> dict:
    """Return the full computed stats context for the current user."""
    return build_user_stats_context(db, _DEFAULT_USER_ID)
