"""Stats router — returns computed statistics for the dashboard and LLM context."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models.user import UserProfile
from app.services.stats import build_user_stats_context

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("")
def get_stats(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Return the full computed stats context for the current user."""
    return build_user_stats_context(db, current_user.id)
