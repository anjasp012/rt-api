import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (
    Table,
    Column,
    Integer,
    String,
    Boolean,
    Text,
    ForeignKey,
    JSON,
    DateTime,
    func
)
from sqlalchemy.orm import relationship
from app.db.session import Base

# Association Table: Solusi <-> Tantangan Relevan (M2M)
solution_relevant_challenges = Table(
    "solution_relevant_challenges",
    Base.metadata,
    Column("solution_id", UUID(as_uuid=True), ForeignKey("solutions.id", ondelete="CASCADE"), primary_key=True),
    Column("challenge_id", UUID(as_uuid=True), ForeignKey("challenges.id", ondelete="CASCADE"), primary_key=True),
)

# Association Table: Solusi <-> Kategori Peran (M2M)
solution_personas = Table(
    "solution_personas",
    Base.metadata,
    Column("solution_id", UUID(as_uuid=True), ForeignKey("solutions.id", ondelete="CASCADE"), primary_key=True),
    Column("persona_id", UUID(as_uuid=True), ForeignKey("personas.id", ondelete="CASCADE"), primary_key=True),
)


class Solution(Base):
    __tablename__ = "solutions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # 1. Nomor urut kartu pertanyaan (opsional)
    card_no = Column(Integer, nullable=True, index=True)

    # 2. Relasi Tantangan / Bidang Utama
    challenge_id = Column(UUID(as_uuid=True), ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True)

    # Optional single-persona relation (kept for backwards compatibility)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("personas.id", ondelete="SET NULL"), nullable=True, index=True)

    # 3. Kartu pertanyaan & pengantar
    question = Column(Text, nullable=True)          # Pertanyaan (e.g. "Bagaimana membuat sapi lokal lebih produktif?")
    card_icon = Column(String(100), nullable=True)  # Ikon kartu (e.g. "cow", "fish")
    introduction = Column(Text, nullable=True)      # Pengantar

    # 4. Aspek penelitian
    aspect = Column(String(255), nullable=True)        # Aspek (e.g. "Kecerdasan buatan", "Bobot badan")
    aspect_icon = Column(String(100), nullable=True)   # Ikon aspek (e.g. "robot-outline", "scale-balance")
    summary = Column(Text, nullable=True)              # Ringkasan (disusun dari abstrak)

    # 5. Metadata publikasi & karya ilmiah
    publication_id = Column(String(100), nullable=True, index=True)  # ID publikasi (e.g. "P10212")
    title = Column(Text, nullable=False, index=True)                 # Judul asli karya ilmiah
    slug = Column(String(255), unique=True, index=True, nullable=False)
    year = Column(Integer, nullable=True)                            # Tahun (e.g. 2025)
    writer = Column(Text, nullable=True)                             # Penulis / Writer (Author)
    publication_media = Column(String(255), nullable=True)           # Media Publikasi / Publication Media
    research_center = Column(Text, nullable=True)                    # Pusat riset penulis (bisa multiple dipisah titik koma)
    journal_publication = Column(String(255), nullable=True)         # Jurnal / terbitan (legacy alias)
    doi = Column(String(255), nullable=True)                         # DOI
    abstract_url = Column(Text, nullable=True)                       # Halaman abstrak yang dibaca (URL)
    access_type = Column(String(100), nullable=True)                 # Akses (e.g. "Open access (CC BY-SA 4.0)")
    author_proof = Column(Text, nullable=True)                       # Bukti karya periset BRIN
    verification_notes = Column(Text, nullable=True)                 # Catatan verifikasi

    # 6. Tahukah kamu? (Fun fact interaktif)
    fun_fact = Column(Text, nullable=True)                           # Tahukah kamu?
    fun_fact_source = Column(String(255), nullable=True)             # Sumber "Tahukah kamu?"
    fun_fact_url = Column(Text, nullable=True)                       # Tautan sumber

    # 7. Informasi pendukung meja interaktif
    trl = Column(Integer, default=7, nullable=False)
    short_description = Column(Text, nullable=True)
    impact = Column(Text, nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    implementation_potential = Column(JSON, default=list, nullable=True)
    relevant_tags = Column(JSON, default=list, nullable=True)
    media_gallery = Column(JSON, default=list, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # --- Relationships ---
    # Tantangan Utama
    challenge = relationship("Challenge", foreign_keys=[challenge_id], back_populates="solutions")

    # Tantangan Relevan (Relasi Many-to-Many dengan Challenge)
    relevant_challenges = relationship(
        "Challenge",
        secondary=solution_relevant_challenges,
        back_populates="relevant_solutions"
    )

    # Kategori Peran (Relasi Many-to-Many dengan Persona)
    personas = relationship(
        "Persona",
        secondary=solution_personas,
        back_populates="solutions"
    )

    # Legacy persona direct relationship
    persona = relationship("Persona", foreign_keys=[persona_id])
    persona_relevances = relationship("SolutionPersonaRelevance", back_populates="solution", cascade="all, delete-orphan")

    # --- Properties & Backward Compatibility ---
    @property
    def challenge_name(self):
        return self.challenge.name if self.challenge else None

    @property
    def challenge_color(self):
        return self.challenge.color if self.challenge else None

    @property
    def challenge_icon(self):
        return self.challenge.icon if self.challenge else None

    @property
    def relevant_challenge_names(self):
        return [c.name for c in self.relevant_challenges] if self.relevant_challenges else []

    @property
    def relevant_challenge_ids(self):
        return [c.id for c in self.relevant_challenges] if self.relevant_challenges else []

    @property
    def persona_name(self):
        if self.personas and len(self.personas) > 0:
            return self.personas[0].name
        if self.persona:
            return self.persona.name
        return None

    @property
    def persona_names(self):
        return [p.name for p in self.personas] if self.personas else []

    @property
    def persona_ids(self):
        return [p.id for p in self.personas] if self.personas else []

    # Indonesian alias properties
    @property
    def judul_asli(self):
        return self.title

    @property
    def ringkasan(self):
        return self.summary

    @property
    def aspek(self):
        return self.aspect

    @property
    def tahun(self):
        return self.year

    @property
    def writter(self):
        return self.writer

    @property
    def author(self):
        return self.writer

    @property
    def penulis(self):
        return self.writer

    @property
    def media_publikasi(self):
        return self.publication_media or self.journal_publication

    @property
    def satker(self):
        return self.research_center

    @property
    def research_unit(self):
        return self.research_center

    @property
    def jurnal_publication(self):
        return self.journal_publication

    # Legacy zone properties for backward-compatibility
    @property
    def zone_id(self):
        return self.challenge_id

    @property
    def zone(self):
        return self.challenge

    @property
    def zone_name(self):
        return self.challenge_name

    @property
    def relevant_zones(self):
        return self.relevant_challenges

    @property
    def relevant_zone_names(self):
        return self.relevant_challenge_names

    @property
    def relevant_zone_ids(self):
        return self.relevant_challenge_ids


# Backward compatibility aliases
Innovation = Solution
innovation_relevant_zones = solution_relevant_challenges
innovation_personas = solution_personas
