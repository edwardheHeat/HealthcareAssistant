"""Stats router — returns computed statistics for the dashboard and LLM context."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
<<<<<<< HEAD
from app.dependencies import get_current_user
from app.models.user import UserProfile
=======
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
from app.services.stats import build_user_stats_context

router = APIRouter(prefix="/stats", tags=["stats"])

<<<<<<< HEAD

@router.get("")
def get_stats(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Return the full computed stats context for the current user."""
    return build_user_stats_context(db, current_user.id)
=======
_DEFAULT_USER_ID = 1


@router.get("")
def get_stats(db: Session = Depends(get_db)) -> dict:
    """Return the full computed stats context for the current user."""
    return build_user_stats_context(db, _DEFAULT_USER_ID)
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
