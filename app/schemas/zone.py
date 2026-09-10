import uuid
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class ZoneBase(BaseModel):
    name: str
    slug: str
    description: str
    icon_url: Optional[str] = None

    is_active: bool = True


class ZoneCreate(ZoneBase):
    pass


class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    icon_url: Optional[str] = None

    is_active: Optional[bool] = None


class ZoneResponse(ZoneBase):
    id: uuid.UUID
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
