from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class ResearchCenterBase(BaseModel):
    name: str
    or_name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None


class ResearchCenterCreate(ResearchCenterBase):
    pass


class ResearchCenterUpdate(BaseModel):
    name: Optional[str] = None
    or_name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None


class ResearchCenterResponse(ResearchCenterBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
