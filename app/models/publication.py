import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    DateTime,
    func
)
from app.db.session import Base


class Publication(Base):
    __tablename__ = "publications"

    # Primary key (UUID auto)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Publication ID (e.g. "P10212") — the human-readable identifier from the source data
    publication_id = Column(String(100), nullable=True, unique=True, index=True)

    # Core fields
    title              = Column(Text, nullable=False, index=True)          # Title / Judul
    publication_media  = Column(String(255), nullable=True)                # Media Publikasi
    coverage           = Column(String(255), nullable=True)                # Cakupan (e.g. Nasional, Internasional)
    year               = Column(Integer, nullable=True, index=True)        # Tahun
    source             = Column(String(255), nullable=True)                # Sumber (e.g. Scopus, Sinta)
    brin_author        = Column(Text, nullable=True)                       # Penulis BRIN (bisa multiple, pisah titik koma)
    research_center    = Column(Text, nullable=True)                       # Pusat Riset / Satker
    field              = Column(String(255), nullable=True)                # Bidang (Field / Research Area)
    province           = Column(String(255), nullable=True)                # Provinsi
    region             = Column(String(255), nullable=True)                # Wilayah
    data_notes         = Column(Text, nullable=True)                       # Catatan data
    is_counted         = Column(Boolean, default=True, nullable=False)     # Dihitung (counted/included)

    is_active  = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # ---- Indonesian alias properties ----
    @property
    def judul(self):
        return self.title

    @property
    def media_publikasi(self):
        return self.publication_media

    @property
    def cakupan(self):
        return self.coverage

    @property
    def tahun(self):
        return self.year

    @property
    def sumber(self):
        return self.source

    @property
    def penulis_brin(self):
        return self.brin_author

    @property
    def pusat_riset(self):
        return self.research_center

    @property
    def satker(self):
        return self.research_center

    @property
    def bidang(self):
        return self.field

    @property
    def wilayah(self):
        return self.region

    @property
    def catatan_data(self):
        return self.data_notes

    @property
    def dihitung(self):
        return self.is_counted
