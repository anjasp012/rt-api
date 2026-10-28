import uuid
from typing import Optional, List
from pydantic import BaseModel, Field, AliasChoices
from datetime import datetime
from app.schemas.challenge import ChallengeResponse, ZoneResponse
from app.schemas.persona import PersonaResponse


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

    class Config:
        from_attributes = True


class SolutionExploreCard(BaseModel):
    id: uuid.UUID
    slug: str
    title: str = Field(..., validation_alias=AliasChoices('title', 'judul_asli'))
    summary: Optional[str] = Field(None, validation_alias=AliasChoices('summary', 'ringkasan'))
    aspect: Optional[str] = Field(None, validation_alias=AliasChoices('aspect', 'aspek'))
    writer: Optional[str] = Field(None, validation_alias=AliasChoices('writer', 'writter', 'author', 'penulis'))
    year: Optional[int] = Field(None, validation_alias=AliasChoices('year', 'tahun'))
    research_center: Optional[str] = Field(None, validation_alias=AliasChoices('research_center', 'satker', 'research_unit'))
    publication_media: Optional[str] = Field(None, validation_alias=AliasChoices('publication_media', 'media_publikasi'))
    abstract_url: Optional[str] = None
    journal_publication: Optional[str] = Field(None, validation_alias=AliasChoices('journal_publication', 'jurnal_publication'))
    question: Optional[str] = Field(None, validation_alias=AliasChoices('question', 'pertanyaan'))
    introduction: Optional[str] = Field(None, validation_alias=AliasChoices('introduction', 'pengantar'))
    challenge_id: Optional[uuid.UUID] = Field(None, validation_alias=AliasChoices('challenge_id', 'challange_id', 'zone_id'))
    challenge_name: Optional[str] = Field(None, validation_alias=AliasChoices('challenge_name', 'challange_name', 'nama_challenge', 'nama_challange'))
    persona_id: Optional[uuid.UUID] = None
    persona_name: Optional[str] = Field(None, validation_alias=AliasChoices('persona_name', 'nama_persona'))
    fun_fact: Optional[str] = Field(None, validation_alias=AliasChoices('fun_fact', 'tahukah_kamu'))
    relevant_challenges: List[str] = Field(default_factory=list, validation_alias=AliasChoices('relevant_challenges', 'bidang_relevan', 'relevant_challenge_names'))
    personas: List[str] = Field(default_factory=list, validation_alias=AliasChoices('personas', 'persona', 'persona_names', 'persona_list'))
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class SolutionDetailResponse(BaseModel):
    id: uuid.UUID
    slug: Optional[str] = None
    title: str = Field(..., validation_alias=AliasChoices('title', 'judul_asli'))
    summary: Optional[str] = Field(None, validation_alias=AliasChoices('summary', 'ringkasan'))
    aspect: Optional[str] = Field(None, validation_alias=AliasChoices('aspect', 'aspek'))
    writer: Optional[str] = Field(None, validation_alias=AliasChoices('writer', 'writter', 'author', 'penulis'))
    year: Optional[int] = Field(None, validation_alias=AliasChoices('year', 'tahun'))
    research_center: Optional[str] = Field(None, validation_alias=AliasChoices('research_center', 'satker', 'research_unit'))
    publication_media: Optional[str] = Field(None, validation_alias=AliasChoices('publication_media', 'media_publikasi'))
    abstract_url: Optional[str] = None
    journal_publication: Optional[str] = Field(None, validation_alias=AliasChoices('journal_publication', 'jurnal_publication'))
    question: Optional[str] = Field(None, validation_alias=AliasChoices('question', 'pertanyaan'))
    introduction: Optional[str] = Field(None, validation_alias=AliasChoices('introduction', 'pengantar'))
    challenge_id: Optional[uuid.UUID] = Field(None, validation_alias=AliasChoices('challenge_id', 'challange_id', 'zone_id'))
    challenge_name: Optional[str] = Field(None, validation_alias=AliasChoices('challenge_name', 'challange_name', 'nama_challenge', 'nama_challange'))
    persona_id: Optional[uuid.UUID] = None
    persona_name: Optional[str] = Field(None, validation_alias=AliasChoices('persona_name', 'nama_persona'))
    fun_fact: Optional[str] = Field(None, validation_alias=AliasChoices('fun_fact', 'tahukah_kamu'))
    relevant_challenges: List[str] = Field(default_factory=list, validation_alias=AliasChoices('relevant_challenges', 'bidang_relevan', 'relevant_challenge_names'))
    personas: List[str] = Field(default_factory=list, validation_alias=AliasChoices('personas', 'persona', 'persona_names', 'persona_list'))
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

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
