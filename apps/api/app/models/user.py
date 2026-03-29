<<<<<<< HEAD
from sqlalchemy import Boolean, CheckConstraint, String
=======
from sqlalchemy import CheckConstraint, String
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    account_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    age: Mapped[int] = mapped_column()
    # "M" or "F"
    sex: Mapped[str] = mapped_column(
        String(1),
        CheckConstraint("sex IN ('M', 'F')", name="ck_sex"),
    )
<<<<<<< HEAD
    # Set to True after the user completes the onboarding questionnaire
    onboarding_complete: Mapped[bool] = mapped_column(Boolean, default=False)
=======
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
