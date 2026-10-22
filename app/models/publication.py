import uuid
import json
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    DateTime,
    JSON,
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
    brin_author        = Column(JSON, nullable=True, default=list)         # Penulis BRIN (JSON array: ["Author 1", "Author 2"])
    research_center    = Column(JSON, nullable=True, default=list)         # Pusat Riset / Satker (JSON array: ["PR 1", "PR 2"])
    field              = Column(JSON, nullable=True, default=list)         # Bidang (JSON array: ["Bidang 1", "Bidang 2"])
    province           = Column(String(255), nullable=True)                # Provinsi
    region             = Column(String(255), nullable=True)                # Wilayah
    data_notes         = Column(Text, nullable=True)                       # Catatan data
    is_counted         = Column(Boolean, default=True, nullable=False)     # Dihitung (counted/included)

    is_active  = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @staticmethod
    def _to_list(val):
        if val is None:
            return []
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            v = val.strip()
            if not v:
                return []
            if v.startswith('[') and v.endswith(']'):
                try:
                    p = json.loads(v)
                    if isinstance(p, list):
                        return p
                except Exception:
                    pass
            return [x.strip() for x in v.split(';') if x.strip()]
        return []

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
        return self._to_list(self.brin_author)

    @property
    def pusat_riset(self):
        return self._to_list(self.research_center)

    @property
    def satker(self):
        return self._to_list(self.research_center)

    @property
    def bidang(self):
        return self._to_list(self.field)

    @property
    def wilayah(self):
        return self.region

    @property
    def catatan_data(self):
        return self.data_notes

    @property
    def dihitung(self):
        return self.is_counted
