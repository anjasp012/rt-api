from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class ZoneBase(BaseModel):
    zone_number: int
    name: str
    slug: str
    description: str
    color_theme: Optional[str] = None
    icon_name: Optional[str] = None
    order_index: int = 0
    is_active: bool = True


class ZoneCreate(ZoneBase):
    pass


class ZoneUpdate(BaseModel):
    zone_number: Optional[int] = None
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    color_theme: Optional[str] = None
    icon_name: Optional[str] = None
    order_index: Optional[int] = None
    is_active: Optional[bool] = None


class ZoneResponse(ZoneBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
