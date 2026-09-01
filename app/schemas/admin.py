from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class BulkStatusUpdate(BaseModel):
    ids: List[int]
    status: str


class BulkDeleteRequest(BaseModel):
    ids: List[int]


class SettingsUpdate(BaseModel):
    frontend_display_limit: Optional[int] = 50
    allow_visitor_submissions: Optional[bool] = True


class DashboardAnalyticsResponse(BaseModel):
    total_innovations: int
    total_personas: int
    total_zones: int
    total_suggestions: int
    new_suggestions: int
    reviewed_suggestions: int
    top_zones: List[Dict[str, Any]]
    top_personas: List[Dict[str, Any]]
    trl_distribution: Dict[str, int]
