from pydantic import BaseModel, Field


class UserProfileCreate(BaseModel):
    name: str = Field(..., max_length=120)
    account_id: str = Field(..., max_length=80)
    password: str = Field(..., min_length=8)
    age: int = Field(..., ge=1, le=130)
    sex: str = Field(..., pattern="^[MF]$")


class UserProfileRead(BaseModel):
    id: int
    name: str
    account_id: str
    age: int
    sex: str
    onboarding_complete: bool

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    account_id: str
    password: str


class LoginResponse(BaseModel):
    user_id: int
    name: str
    onboarding_complete: bool


class OnboardingComplete(BaseModel):
    """Payload sent when the user finishes the onboarding questionnaire."""
    injuries: str | None = None
    surgeries: str | None = None
    constraints: str | None = None
