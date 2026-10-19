import uuid
from typing import Optional
from pydantic import BaseModel, field_validator
from datetime import datetime
from app.core.helpers import build_full_url


class ChallengeBase(BaseModel):
    name: str
    slug: str
    color: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    icon_url: Optional[str] = None
    is_active: bool = True


class ChallengeCreate(ChallengeBase):
    pass


class ChallengeUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    icon_url: Optional[str] = None
    is_active: Optional[bool] = None


class ChallengeResponse(ChallengeBase):
    id: uuid.UUID
    created_at: Optional[datetime] = None

    @field_validator("icon_url", mode="after")
    @classmethod
    def format_icon_url(cls, v: Optional[str]) -> Optional[str]:
        return build_full_url(v)

    class Config:
        from_attributes = True


# Aliases untuk backward compatibility
ZoneBase = ChallengeBase
ZoneCreate = ChallengeCreate
ZoneUpdate = ChallengeUpdate
ZoneResponse = ChallengeResponse
