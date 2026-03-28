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

    model_config = {"from_attributes": True}
