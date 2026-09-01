from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class PersonaBase(BaseModel):
    name: str
    slug: str
    tagline: str
    icon_name: Optional[str] = None
    avatar_url: Optional[str] = None
    order_index: int = 0
    is_active: bool = True


class PersonaCreate(PersonaBase):
    pass


class PersonaUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    tagline: Optional[str] = None
    icon_name: Optional[str] = None
    avatar_url: Optional[str] = None
    order_index: Optional[int] = None
    is_active: Optional[bool] = None


class PersonaResponse(PersonaBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
