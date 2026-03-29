"""User profile router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models.user import UserProfile
from app.schemas.user import UserLoginRequest, UserProfileCreate, UserSessionRead
from app.services.accounts import (
    authenticate_user,
    build_user_session,
    create_user_account,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserSessionRead, status_code=201)
def create_user(
    payload: UserProfileCreate,
    db: Session = Depends(get_db),
) -> UserSessionRead:
    existing = db.scalars(
        select(UserProfile).where(UserProfile.account_id == payload.account_id)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Account ID already exists.")

    user = create_user_account(db, payload)
    return build_user_session(db, user)


@router.post("/login", response_model=UserSessionRead)
def login_user(
    payload: UserLoginRequest,
    db: Session = Depends(get_db),
) -> UserSessionRead:
    user = authenticate_user(db, payload)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid account ID or password.")
    return build_user_session(db, user)


@router.get("/me", response_model=UserSessionRead)
def get_me(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserSessionRead:
    return build_user_session(db, current_user)
