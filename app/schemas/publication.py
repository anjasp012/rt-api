import uuid
import json
from typing import Optional, List, Union
from pydantic import BaseModel, Field, AliasChoices, field_validator
from datetime import datetime


def _parse_list_input(v):
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    if isinstance(v, str):
        v_str = v.strip()
        if not v_str:
            return []
        if v_str.startswith('[') and v_str.endswith(']'):
            try:
                parsed = json.loads(v_str)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except Exception:
                pass
        return [x.strip() for x in v_str.split(';') if x.strip()]
    return []


class PublicationBase(BaseModel):
    publication_id:    Optional[str]        = None
    title:             str                  = Field(..., validation_alias=AliasChoices('title', 'judul'))
    publication_media: Optional[str]        = Field(None, validation_alias=AliasChoices('publication_media', 'media_publikasi'))
    coverage:          Optional[str]        = Field(None, validation_alias=AliasChoices('coverage', 'cakupan'))
    year:              Optional[int]        = Field(None, validation_alias=AliasChoices('year', 'tahun'))
    source:            Optional[str]        = Field(None, validation_alias=AliasChoices('source', 'sumber'))
    brin_author:       Optional[List[str]]  = Field(default_factory=list, validation_alias=AliasChoices('brin_author', 'penulis_brin'))
    research_center:   Optional[List[str]]  = Field(default_factory=list, validation_alias=AliasChoices('research_center', 'pusat_riset', 'satker'))
    field:             Optional[List[str]]  = Field(default_factory=list, validation_alias=AliasChoices('field', 'bidang'))
    province:          Optional[str]        = Field(None, validation_alias=AliasChoices('province', 'provinsi'))
    region:            Optional[str]        = Field(None, validation_alias=AliasChoices('region', 'wilayah'))
    data_notes:        Optional[str]        = Field(None, validation_alias=AliasChoices('data_notes', 'catatan_data'))
    is_counted:        bool                 = Field(True, validation_alias=AliasChoices('is_counted', 'dihitung'))
    is_active:         bool                 = True

    @field_validator('brin_author', 'research_center', 'field', mode='before')
    @classmethod
    def validate_list_fields(cls, v):
        return _parse_list_input(v)


class PublicationCreate(PublicationBase):
    pass


class PublicationUpdate(BaseModel):
    publication_id:    Optional[str]        = None
    title:             Optional[str]        = Field(None, validation_alias=AliasChoices('title', 'judul'))
    publication_media: Optional[str]        = Field(None, validation_alias=AliasChoices('publication_media', 'media_publikasi'))
    coverage:          Optional[str]        = Field(None, validation_alias=AliasChoices('coverage', 'cakupan'))
    year:              Optional[int]        = Field(None, validation_alias=AliasChoices('year', 'tahun'))
    source:            Optional[str]        = Field(None, validation_alias=AliasChoices('source', 'sumber'))
    brin_author:       Optional[List[str]]  = Field(None, validation_alias=AliasChoices('brin_author', 'penulis_brin'))
    research_center:   Optional[List[str]]  = Field(None, validation_alias=AliasChoices('research_center', 'pusat_riset', 'satker'))
    field:             Optional[List[str]]  = Field(None, validation_alias=AliasChoices('field', 'bidang'))
    province:          Optional[str]        = Field(None, validation_alias=AliasChoices('province', 'provinsi'))
    region:            Optional[str]        = Field(None, validation_alias=AliasChoices('region', 'wilayah'))
    data_notes:        Optional[str]        = Field(None, validation_alias=AliasChoices('data_notes', 'catatan_data'))
    is_counted:        Optional[bool]       = Field(None, validation_alias=AliasChoices('is_counted', 'dihitung'))
    is_active:         Optional[bool]       = None

    @field_validator('brin_author', 'research_center', 'field', mode='before')
    @classmethod
    def validate_update_list_fields(cls, v):
        if v is None:
            return None
        return _parse_list_input(v)


class PublicationResponse(PublicationBase):
    id: uuid.UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Expose Indonesian aliases in response
    judul:             Optional[str]        = None
    media_publikasi:   Optional[str]        = None
    cakupan:           Optional[str]        = None
    tahun:             Optional[int]        = None
    sumber:            Optional[str]        = None
    penulis_brin:      Optional[List[str]]  = None
    pusat_riset:       Optional[List[str]]  = None
    satker:            Optional[List[str]]  = None
    bidang:            Optional[List[str]]  = None
    provinsi:          Optional[str]        = None
    wilayah:           Optional[str]        = None
    catatan_data:      Optional[str]        = None
    dihitung:          Optional[bool]       = None

    class Config:
        from_attributes = True
        populate_by_name = True
