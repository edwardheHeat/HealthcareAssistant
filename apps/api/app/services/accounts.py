"""Account and lightweight session services."""

from __future__ import annotations

import hashlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.clinical import ClinicalHistory
from app.models.user import UserProfile
from app.schemas.user import UserLoginRequest, UserProfileCreate, UserSessionRead


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def is_onboarding_complete(db: Session, user_id: int) -> bool:
    profile = db.scalars(
        select(ClinicalHistory).where(ClinicalHistory.user_id == user_id).limit(1)
    ).first()
    if profile is None:
        return False
    return any([profile.injuries, profile.surgeries, profile.constraints])


def build_user_session(db: Session, user: UserProfile) -> UserSessionRead:
    return UserSessionRead(
        id=user.id,
        name=user.name,
        account_id=user.account_id,
        age=user.age,
        sex=user.sex,
        onboarding_complete=is_onboarding_complete(db, user.id),
    )


def create_user_account(db: Session, payload: UserProfileCreate) -> UserProfile:
    user = UserProfile(
        name=payload.name,
        account_id=payload.account_id,
        password_hash=_hash_password(payload.password),
        age=payload.age,
        sex=payload.sex,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, payload: UserLoginRequest) -> UserProfile | None:
    user = db.scalars(
        select(UserProfile).where(UserProfile.account_id == payload.account_id)
    ).first()
    if user is None:
        return None
    if user.password_hash != _hash_password(payload.password):
        return None
    return user
