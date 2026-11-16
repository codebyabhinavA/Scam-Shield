from typing import Annotated
from pydantic import StringConstraints
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
MessageText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=5, max_length=5000)
]


class CheckCreate(BaseModel):
    message_text: MessageText


class RedFlag(BaseModel):
    type: str
    explanation: str


class CheckSummary(BaseModel):
    id: int
    risk_level: str
    summary: str | None
    feedback: str | None
    created_at: datetime


class CheckDetail(CheckSummary):
    message_text: str
    next_steps: str | None
    red_flags: list[RedFlag]