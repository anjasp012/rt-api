import uuid
from typing import Optional
from pydantic import BaseModel, Field, AliasChoices
from datetime import datetime


class PublicationBase(BaseModel):
    # Human-readable publication ID (e.g. "P10212")
    publication_id: Optional[str] = None

    # Core fields
    title:             str                  = Field(..., validation_alias=AliasChoices('title', 'judul'))
    publication_media: Optional[str]        = Field(None, validation_alias=AliasChoices('publication_media', 'media_publikasi'))
    coverage:          Optional[str]        = Field(None, validation_alias=AliasChoices('coverage', 'cakupan'))
    year:              Optional[int]        = Field(None, validation_alias=AliasChoices('year', 'tahun'))
    source:            Optional[str]        = Field(None, validation_alias=AliasChoices('source', 'sumber'))
    brin_author:       Optional[str]        = Field(None, validation_alias=AliasChoices('brin_author', 'penulis_brin'))
    research_center:   Optional[str]        = Field(None, validation_alias=AliasChoices('research_center', 'pusat_riset', 'satker'))
    field:             Optional[str]        = Field(None, validation_alias=AliasChoices('field', 'bidang'))
    province:          Optional[str]        = Field(None, validation_alias=AliasChoices('province', 'provinsi'))
    region:            Optional[str]        = Field(None, validation_alias=AliasChoices('region', 'wilayah'))
    data_notes:        Optional[str]        = Field(None, validation_alias=AliasChoices('data_notes', 'catatan_data'))
    is_counted:        bool                 = Field(True, validation_alias=AliasChoices('is_counted', 'dihitung'))
    is_active:         bool                 = True


class PublicationCreate(PublicationBase):
    pass


class PublicationUpdate(BaseModel):
    publication_id:    Optional[str]  = None
    title:             Optional[str]  = Field(None, validation_alias=AliasChoices('title', 'judul'))
    publication_media: Optional[str]  = Field(None, validation_alias=AliasChoices('publication_media', 'media_publikasi'))
    coverage:          Optional[str]  = Field(None, validation_alias=AliasChoices('coverage', 'cakupan'))
    year:              Optional[int]  = Field(None, validation_alias=AliasChoices('year', 'tahun'))
    source:            Optional[str]  = Field(None, validation_alias=AliasChoices('source', 'sumber'))
    brin_author:       Optional[str]  = Field(None, validation_alias=AliasChoices('brin_author', 'penulis_brin'))
    research_center:   Optional[str]  = Field(None, validation_alias=AliasChoices('research_center', 'pusat_riset', 'satker'))
    field:             Optional[str]  = Field(None, validation_alias=AliasChoices('field', 'bidang'))
    province:          Optional[str]  = Field(None, validation_alias=AliasChoices('province', 'provinsi'))
    region:            Optional[str]  = Field(None, validation_alias=AliasChoices('region', 'wilayah'))
    data_notes:        Optional[str]  = Field(None, validation_alias=AliasChoices('data_notes', 'catatan_data'))
    is_counted:        Optional[bool] = Field(None, validation_alias=AliasChoices('is_counted', 'dihitung'))
    is_active:         Optional[bool] = None


class PublicationResponse(PublicationBase):
    id: uuid.UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Expose Indonesian aliases in response too
    judul:             Optional[str]  = None
    media_publikasi:   Optional[str]  = None
    cakupan:           Optional[str]  = None
    tahun:             Optional[int]  = None
    sumber:            Optional[str]  = None
    penulis_brin:      Optional[str]  = None
    pusat_riset:       Optional[str]  = None
    satker:            Optional[str]  = None
    bidang:            Optional[str]  = None
    provinsi:          Optional[str]  = None
    wilayah:           Optional[str]  = None
    catatan_data:      Optional[str]  = None
    dihitung:          Optional[bool] = None

    class Config:
        from_attributes = True
        populate_by_name = True
