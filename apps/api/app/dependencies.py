"""Shared FastAPI dependencies."""

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import UserProfile


def get_current_user(
    x_user_id: int | None = Header(None, alias="X-User-ID"),
    db: Session = Depends(get_db),
) -> UserProfile:
    """Resolve the authenticated user from the X-User-ID request header.

    The frontend stores the user's ID in localStorage after login and sends it
    as this header on every request. For an MVP this is sufficient; a production
    system should use signed JWT tokens instead.
    """
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Missing user credentials.")
    user = db.get(UserProfile, x_user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid user credentials.")
    return user
