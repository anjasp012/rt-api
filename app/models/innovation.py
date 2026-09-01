from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, JSON, DateTime, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Innovation(Base):
    __tablename__ = "innovations"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True)
    research_center_id = Column(Integer, ForeignKey("research_centers.id", ondelete="SET NULL"), nullable=True, index=True)
    
    title = Column(String(255), index=True, nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    category_tag = Column(String(100), index=True, nullable=False)
    trl = Column(Integer, default=1, nullable=False)
    
    short_description = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    impact = Column(Text, nullable=False)
    
    thumbnail_url = Column(String(500), nullable=True)
    download_url = Column(String(500), nullable=True)
    qr_code_data = Column(String(500), nullable=True)
    media_gallery = Column(JSON, default=list, nullable=True)
    
    order_priority = Column(Integer, default=0, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    zone = relationship("Zone", back_populates="innovations")
    research_center = relationship("ResearchCenter", back_populates="innovations")
    persona_relevances = relationship("InnovationPersonaRelevance", back_populates="innovation", cascade="all, delete-orphan")
