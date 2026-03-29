"""User profile router."""

import hashlib

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import UserProfile
from app.schemas.user import UserProfileCreate, UserProfileRead

router = APIRouter(prefix="/users", tags=["users"])

# MVP: single user, hardcoded id=1
_DEFAULT_USER_ID = 1


@router.post("", response_model=UserProfileRead, status_code=201)
def create_user(payload: UserProfileCreate, db: Session = Depends(get_db)) -> UserProfile:
    existing = db.scalars(
        select(UserProfile).where(UserProfile.account_id == payload.account_id)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Account ID already exists.")
    user = UserProfile(
        name=payload.name,
        account_id=payload.account_id,
        password_hash=hashlib.sha256(payload.password.encode()).hexdigest(),
        age=payload.age,
        sex=payload.sex,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=UserProfileRead)
def get_me(db: Session = Depends(get_db)) -> UserProfile:
    user = db.get(UserProfile, _DEFAULT_USER_ID)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return user
