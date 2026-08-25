"""
Pydantic schemas -- these define what shape of JSON the API accepts and
returns. Separate from the SQLAlchemy models on purpose: a model describes
a database row (includes hashed_password, internal ids, etc); a schema
describes an API contract (never includes hashed_password, for instance --
that must never leave the server in a response, even by accident).
"""

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    id: int
    email: EmailStr
    name: str

    class Config:
        from_attributes = True  # allows creating this directly from a SQLAlchemy User object