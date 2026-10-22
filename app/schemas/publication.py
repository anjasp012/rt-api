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


# =========================================================================
# 📊 PUBLIC OVERVIEW & HAMPARAN SCHEMAS
# =========================================================================

class HamparanItem(BaseModel):
    id_publication: str
    publication_id: Optional[str] = None
    is_active: bool


class YearlyTrendItem(BaseModel):
    year: int
    count: int


class CenterCountItem(BaseModel):
    name: str
    count: int


class FieldCountItem(BaseModel):
    name: str
    count: int


class FilterState(BaseModel):
    year: Optional[int] = None
    field: Optional[str] = None


class PublicPublicationOverviewResponse(BaseModel):
    total_publications: int = Field(..., description="Total publikasi ilmiah riil di database")
    total_researchers: int = Field(..., description="Total penulis unik afiliasi BRIN")
    total_research_centers: int = Field(..., description="Total pusat riset / satker unik terpetakan")
    min_year: int = Field(..., description="Tahun terawal dari data yang ada")
    since_year: int = Field(..., description="Tahun patokan aktif")
    count_since_year: int = Field(..., description="Jumlah publikasi sejak since_year (sesuai filter bidang)")
    count_all_years: int = Field(..., description="Jumlah publikasi seluruh tahun (sesuai filter bidang)")
    yearly_trend: List[YearlyTrendItem] = Field(default_factory=list, description="Jejak publikasi per tahun")
    top_centers: List[CenterCountItem] = Field(default_factory=list, description="Top 3 pusat riset terbanyak")
    total_fields: int = Field(..., description="Total bidang riset unik")
    fields: List[FieldCountItem] = Field(default_factory=list, description="Daftar seluruh bidang dan total publikasinya")
    filter: FilterState = Field(..., description="Status filter yang sedang aktif")
    hamparan: List[HamparanItem] = Field(default_factory=list, description="Daftar seluruh titik publikasi dengan status boolean is_active")
