import uuid
from typing import Optional, List
from pydantic import BaseModel, Field, AliasChoices, field_validator
from datetime import datetime
from app.schemas.challenge import ChallengeResponse, ZoneResponse
from app.schemas.persona import PersonaResponse
from app.core.helpers import build_full_url, build_full_url_list


class SolutionBase(BaseModel):
    # 1. Kartu & Nomor
    card_no: Optional[int] = None

    # 2. Relasi Tantangan / Bidang Utama
    challenge_id: uuid.UUID = Field(..., validation_alias=AliasChoices('challenge_id', 'zone_id'))

    # Optional relasi persona tunggal (legacy)
    persona_id: Optional[uuid.UUID] = None

    # Multi-pilih Tantangan Relevan & Kategori Peran
    relevant_challenge_ids: Optional[List[uuid.UUID]] = Field(default=[], validation_alias=AliasChoices('relevant_challenge_ids', 'relevant_zone_ids'))
    persona_ids: Optional[List[uuid.UUID]] = []

    # 3. Kartu pertanyaan & pengantar
    question: Optional[str] = None
    card_icon: Optional[str] = None
    introduction: Optional[str] = None

    # 4. Aspek penelitian
    aspect: Optional[str] = None
    aspect_icon: Optional[str] = None
    summary: Optional[str] = None

    # 5. Metadata publikasi & karya ilmiah
    publication_id: Optional[str] = None
    title: str = Field(..., validation_alias=AliasChoices('title', 'judul_asli'))
    slug: str
    year: Optional[int] = Field(None, validation_alias=AliasChoices('year', 'tahun'))
    writer: Optional[str] = Field(None, validation_alias=AliasChoices('writer', 'writter', 'author', 'penulis'))
    publication_media: Optional[str] = Field(None, validation_alias=AliasChoices('publication_media', 'media_publikasi'))
    research_center: Optional[str] = Field(None, validation_alias=AliasChoices('research_center', 'satker', 'research_unit'))
    journal_publication: Optional[str] = Field(None, validation_alias=AliasChoices('journal_publication', 'jurnal_publication'))
    doi: Optional[str] = None
    abstract_url: Optional[str] = None
    access_type: Optional[str] = None
    author_proof: Optional[str] = None
    verification_notes: Optional[str] = None

    # 6. Tahukah kamu?
    fun_fact: Optional[str] = None
    fun_fact_source: Optional[str] = None
    fun_fact_url: Optional[str] = None

    # 7. Informasi pendukung
    trl: int = 7
    short_description: Optional[str] = None
    impact: Optional[str] = None
    thumbnail_url: Optional[str] = None
    implementation_potential: Optional[List[str]] = None
    relevant_tags: Optional[List[str]] = None
    media_gallery: Optional[List[str]] = None
    is_active: bool = True

    # Backward compatibility
    @property
    def zone_id(self):
        return self.challenge_id

    @property
    def relevant_zone_ids(self):
        return self.relevant_challenge_ids


class SolutionCreate(SolutionBase):
    pass


class SolutionUpdate(BaseModel):
    card_no: Optional[int] = None
    challenge_id: Optional[uuid.UUID] = Field(None, validation_alias=AliasChoices('challenge_id', 'zone_id'))
    persona_id: Optional[uuid.UUID] = None
    relevant_challenge_ids: Optional[List[uuid.UUID]] = Field(None, validation_alias=AliasChoices('relevant_challenge_ids', 'relevant_zone_ids'))
    persona_ids: Optional[List[uuid.UUID]] = None

    question: Optional[str] = None
    card_icon: Optional[str] = None
    introduction: Optional[str] = None

    aspect: Optional[str] = None
    aspect_icon: Optional[str] = None
    summary: Optional[str] = None

    publication_id: Optional[str] = None
    title: Optional[str] = Field(None, validation_alias=AliasChoices('title', 'judul_asli'))
    slug: Optional[str] = None
    year: Optional[int] = Field(None, validation_alias=AliasChoices('year', 'tahun'))
    writer: Optional[str] = Field(None, validation_alias=AliasChoices('writer', 'writter', 'author', 'penulis'))
    publication_media: Optional[str] = Field(None, validation_alias=AliasChoices('publication_media', 'media_publikasi'))
    research_center: Optional[str] = Field(None, validation_alias=AliasChoices('research_center', 'satker', 'research_unit'))
    journal_publication: Optional[str] = Field(None, validation_alias=AliasChoices('journal_publication', 'jurnal_publication'))
    doi: Optional[str] = None
    abstract_url: Optional[str] = None
    access_type: Optional[str] = None
    author_proof: Optional[str] = None
    verification_notes: Optional[str] = None

    fun_fact: Optional[str] = None
    fun_fact_source: Optional[str] = None
    fun_fact_url: Optional[str] = None

    trl: Optional[int] = None
    short_description: Optional[str] = None
    impact: Optional[str] = None
    thumbnail_url: Optional[str] = None
    implementation_potential: Optional[List[str]] = None
    relevant_tags: Optional[List[str]] = None
    media_gallery: Optional[List[str]] = None
    is_active: Optional[bool] = None


class RelevanceMappingItem(BaseModel):
    persona_id: uuid.UUID
    relevance_score: int
    custom_impact: Optional[str] = None


class SolutionResponse(SolutionBase):
    id: uuid.UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    challenge: Optional[ChallengeResponse] = None
    challenge_name: Optional[str] = None

    relevant_challenges: Optional[List[ChallengeResponse]] = []
    relevant_challenge_names: Optional[List[str]] = []
    relevant_challenge_ids: Optional[List[uuid.UUID]] = []

    personas: Optional[List[PersonaResponse]] = []
    persona_names: Optional[List[str]] = []
    persona_ids: Optional[List[uuid.UUID]] = []

    persona: Optional[PersonaResponse] = None
    persona_name: Optional[str] = None

    # Backward compatibility zone & alias fields
    satker: Optional[str] = None
    author: Optional[str] = None
    media_publikasi: Optional[str] = None
    zone: Optional[ZoneResponse] = None
    zone_name: Optional[str] = None
    relevant_zones: Optional[List[ZoneResponse]] = []
    relevant_zone_names: Optional[List[str]] = []

    @field_validator("thumbnail_url", mode="after")
    @classmethod
    def format_thumbnail_url(cls, v: Optional[str]) -> Optional[str]:
        return build_full_url(v)

    @field_validator("media_gallery", mode="after")
    @classmethod
    def format_media_gallery(cls, v: Optional[List[str]]) -> List[str]:
        return build_full_url_list(v)

    class Config:
        from_attributes = True


class SolutionExploreCard(BaseModel):
    id: uuid.UUID
    slug: str
    judul_asli: str = Field(..., validation_alias=AliasChoices('judul_asli', 'title'))
    ringkasan: Optional[str] = Field(None, validation_alias=AliasChoices('ringkasan', 'summary'))
    aspek: Optional[str] = Field(None, validation_alias=AliasChoices('aspek', 'aspect'))
    tahun: Optional[int] = Field(None, validation_alias=AliasChoices('tahun', 'year'))
    writer: Optional[str] = Field(None, validation_alias=AliasChoices('writer', 'writter', 'author', 'penulis'))
    publication_media: Optional[str] = Field(None, validation_alias=AliasChoices('publication_media', 'media_publikasi'))
    research_center: Optional[str] = Field(None, validation_alias=AliasChoices('research_center', 'satker', 'research_unit'))
    satker: Optional[str] = None
    author: Optional[str] = None
    media_publikasi: Optional[str] = None
    pertanyaan: Optional[str] = Field(None, validation_alias=AliasChoices('pertanyaan', 'question'))
    pengantar: Optional[str] = Field(None, validation_alias=AliasChoices('pengantar', 'introduction'))
    challenge_name: Optional[str] = Field(None, validation_alias=AliasChoices('challenge_name', 'challange_name', 'nama_challenge', 'nama_challange'))
    challange_name: Optional[str] = Field(None, validation_alias=AliasChoices('challange_name', 'challenge_name', 'nama_challange', 'nama_challenge'))
    persona_name: Optional[str] = Field(None, validation_alias=AliasChoices('persona_name', 'nama_persona'))
    nama_challenge: Optional[str] = Field(None, validation_alias=AliasChoices('nama_challenge', 'nama_challange', 'challenge_name', 'challange_name'))
    nama_persona: Optional[str] = Field(None, validation_alias=AliasChoices('nama_persona', 'persona_name'))

    class Config:
        from_attributes = True
        populate_by_name = True


class SolutionDetailResponse(BaseModel):
    id: uuid.UUID
    title: str = Field(..., validation_alias=AliasChoices('title', 'judul_asli'))
    summary: Optional[str] = Field(None, validation_alias=AliasChoices('summary', 'ringkasan'))
    aspek: Optional[str] = Field(None, validation_alias=AliasChoices('aspek', 'aspect'))
    writter: Optional[str] = Field(None, validation_alias=AliasChoices('writter', 'writer', 'author', 'penulis'))
    year: Optional[int] = Field(None, validation_alias=AliasChoices('year', 'tahun'))
    research_center: Optional[str] = Field(None, validation_alias=AliasChoices('research_center', 'satker'))
    publication_media: Optional[str] = Field(None, validation_alias=AliasChoices('publication_media', 'media_publikasi'))
    abstract_url: Optional[str] = None
    jurnal_publication: Optional[str] = Field(None, validation_alias=AliasChoices('jurnal_publication', 'journal_publication'))
    bidang_relevan: List[str] = Field(default_factory=list, validation_alias=AliasChoices('bidang_relevan', 'relevant_challenges', 'relevant_challenge_names'))
    persona: List[str] = Field(default_factory=list, validation_alias=AliasChoices('persona', 'personas', 'persona_names', 'persona_list'))
    challenge_name: Optional[str] = Field(None, validation_alias=AliasChoices('challenge_name', 'challange_name', 'nama_challenge', 'nama_challange'))
    challange_name: Optional[str] = Field(None, validation_alias=AliasChoices('challange_name', 'challenge_name', 'nama_challange', 'nama_challenge'))
    persona_name: Optional[str] = Field(None, validation_alias=AliasChoices('persona_name', 'nama_persona'))
    nama_challenge: Optional[str] = Field(None, validation_alias=AliasChoices('nama_challenge', 'nama_challange', 'challenge_name', 'challange_name'))
    nama_persona: Optional[str] = Field(None, validation_alias=AliasChoices('nama_persona', 'persona_name'))
    pertanyaan: Optional[str] = Field(None, validation_alias=AliasChoices('pertanyaan', 'question'))
    pengantar: Optional[str] = Field(None, validation_alias=AliasChoices('pengantar', 'introduction'))

    class Config:
        from_attributes = True
        populate_by_name = True


# Aliases untuk backward compatibility
InnovationBase = SolutionBase
InnovationCreate = SolutionCreate
InnovationUpdate = SolutionUpdate
InnovationResponse = SolutionResponse
InnovationExploreCard = SolutionExploreCard
InnovationDetailResponse = SolutionDetailResponse
