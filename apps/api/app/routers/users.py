"""User profile router — signup, login, onboarding."""

import hashlib

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models.clinical import ClinicalHistory
from app.models.user import UserProfile
from app.schemas.user import (
    LoginRequest,
    LoginResponse,
    OnboardingComplete,
    UserProfileCreate,
    UserProfileRead,
)

router = APIRouter(prefix="/users", tags=["users"])


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


@router.post("", response_model=UserProfileRead, status_code=201)
def create_user(payload: UserProfileCreate, db: Session = Depends(get_db)) -> UserProfile:
    """Register a new account."""
    existing = db.scalars(
        select(UserProfile).where(UserProfile.account_id == payload.account_id)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Account ID already taken.")
    user = UserProfile(
        name=payload.name,
        account_id=payload.account_id,
        password_hash=_hash_password(payload.password),
        age=payload.age,
        sex=payload.sex,
        onboarding_complete=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    """Authenticate and return the user's ID for client-side storage."""
    user = db.scalars(
        select(UserProfile).where(UserProfile.account_id == payload.account_id)
    ).first()
    if user is None or user.password_hash != _hash_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid account ID or password.")
    return LoginResponse(
        user_id=user.id,
        name=user.name,
        onboarding_complete=user.onboarding_complete,
    )


@router.get("/me", response_model=UserProfileRead)
def get_me(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
    """Return the authenticated user's profile."""
    return current_user


@router.post("/onboarding", response_model=UserProfileRead)
def complete_onboarding(
    payload: OnboardingComplete,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfile:
    """Save clinical history from onboarding and mark onboarding complete."""
    # Upsert clinical history
    history = db.scalars(
        select(ClinicalHistory).where(ClinicalHistory.user_id == current_user.id)
    ).first()
    if history is None:
        history = ClinicalHistory(
            user_id=current_user.id,
            injuries=payload.injuries,
            surgeries=payload.surgeries,
            constraints=payload.constraints,
        )
        db.add(history)
    else:
        history.injuries = payload.injuries
        history.surgeries = payload.surgeries
        history.constraints = payload.constraints

    current_user.onboarding_complete = True
    db.commit()
    db.refresh(current_user)
    return current_user
