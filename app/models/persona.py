from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Persona(Base):
    __tablename__ = "personas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    tagline = Column(Text, nullable=False)
    icon_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    order_index = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    relevance_mappings = relationship("InnovationPersonaRelevance", back_populates="persona", cascade="all, delete-orphan")
    suggestions = relationship("ResearchSuggestion", back_populates="persona")
