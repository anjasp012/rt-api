import math
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from app.schemas.zone import ZoneResponse
from app.schemas.research_center import ResearchCenterResponse


class InnovationBase(BaseModel):
    zone_id: int
    research_center_id: Optional[int] = None
    title: str
    slug: str
    category_tag: str
    trl: int = 1
    short_description: str
    summary: str
    impact: str
    thumbnail_url: Optional[str] = None
    download_url: Optional[str] = None
    qr_code_data: Optional[str] = None
    media_gallery: Optional[List[str]] = []
    order_priority: int = 0
    is_featured: bool = False
    is_active: bool = True


class InnovationCreate(InnovationBase):
    pass


class InnovationUpdate(BaseModel):
    zone_id: Optional[int] = None
    research_center_id: Optional[int] = None
    title: Optional[str] = None
    slug: Optional[str] = None
    category_tag: Optional[str] = None
    trl: Optional[int] = None
    short_description: Optional[str] = None
    summary: Optional[str] = None
    impact: Optional[str] = None
    thumbnail_url: Optional[str] = None
    download_url: Optional[str] = None
    qr_code_data: Optional[str] = None
    media_gallery: Optional[List[str]] = None
    order_priority: Optional[int] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None


class RelevanceMappingItem(BaseModel):
    persona_id: int
    relevance_score: int
    custom_impact: Optional[str] = None


class InnovationResponse(InnovationBase):
    id: int
    created_at: Optional[datetime] = None
    zone: Optional[ZoneResponse] = None
    research_center: Optional[ResearchCenterResponse] = None

    class Config:
        from_attributes = True


class InnovationExploreCard(BaseModel):
    id: int
    title: str
    slug: str
    category_tag: str
    trl: int
    short_description: str
    summary: str
    impact: str
    thumbnail_url: Optional[str] = None
    download_url: Optional[str] = None
    qr_code_data: Optional[str] = None
    zone_name: str
    zone_number: int
    research_center_name: Optional[str] = None
    relevance_score: int = 0

    class Config:
        from_attributes = True


class InnovationExplorePaginatedResponse(BaseModel):
    items: List[InnovationExploreCard]
    total: int
    page: int
    page_size: int
    total_pages: int
