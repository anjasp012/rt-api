import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, Boolean, Text, DateTime, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Persona(Base):
    __tablename__ = "personas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(150), unique=True, index=True, nullable=False)
    slug = Column(String(150), unique=True, index=True, nullable=False)
    tagline = Column(Text, nullable=True)
    icon = Column(String(100), nullable=True)
    icon_url = Column(String(500), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    relevance_mappings = relationship("SolutionPersonaRelevance", back_populates="persona", cascade="all, delete-orphan")
    
    # Solusi terkait peran ini (M2M)
    solutions = relationship(
        "Solution",
        secondary="solution_personas",
        back_populates="personas"
    )

    # Backward compatibility alias
    @property
    def innovations(self):
        return self.solutions

    suggestions = relationship("ResearchSuggestion", secondary="suggestion_personas", back_populates="personas")
