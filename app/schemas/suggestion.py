import uuid
from typing import Optional, List
from pydantic import BaseModel, Field, AliasChoices, field_validator
from datetime import datetime


class SuggestionCreate(BaseModel):
    title: str = Field(..., validation_alias=AliasChoices('title', 'topic_wanted'))
    deskripsi: Optional[str] = Field(None, validation_alias=AliasChoices('deskripsi', 'description', 'feedback'))
    persona_ids: Optional[List[uuid.UUID]] = Field(default=[], validation_alias=AliasChoices('persona_ids', 'persona_id'))
    challange_ids: Optional[List[uuid.UUID]] = Field(default=[], validation_alias=AliasChoices('challange_ids', 'challenge_ids', 'challenge_id', 'zone_id'))

    @field_validator('persona_ids', mode='before')
    @classmethod
    def parse_persona_ids(cls, v):
        if v is None:
            return []
        if isinstance(v, (str, uuid.UUID)):
            return [v]
        return v

    @field_validator('challange_ids', mode='before')
    @classmethod
    def parse_challenge_ids(cls, v):
        if v is None:
            return []
        if isinstance(v, (str, uuid.UUID)):
            return [v]
        return v


class SuggestionStatusUpdate(BaseModel):
    status: str
    admin_notes: Optional[str] = None


class SuggestionResponse(BaseModel):
    id: uuid.UUID
    title: str
    deskripsi: Optional[str] = None
    persona_ids: List[uuid.UUID] = []
    challange_ids: List[uuid.UUID] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SuggestionAdminResponse(SuggestionResponse):
    status: Optional[str] = "NEW"
    admin_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    persona_name: Optional[str] = None
    challenge_name: Optional[str] = None
    zone_name: Optional[str] = None
    topic_wanted: Optional[str] = None
    feedback: Optional[str] = None

    class Config:
        from_attributes = True
