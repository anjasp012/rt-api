import uuid
from typing import List
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Table, Column, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.session import Base

# Association Table: ResearchSuggestion <-> Persona (M2M)
suggestion_personas = Table(
    "suggestion_personas",
    Base.metadata,
    Column("suggestion_id", UUID(as_uuid=True), ForeignKey("research_suggestions.id", ondelete="CASCADE"), primary_key=True),
    Column("persona_id", UUID(as_uuid=True), ForeignKey("personas.id", ondelete="CASCADE"), primary_key=True),
)

# Association Table: ResearchSuggestion <-> Challenge (M2M)
suggestion_challenges = Table(
    "suggestion_challenges",
    Base.metadata,
    Column("suggestion_id", UUID(as_uuid=True), ForeignKey("research_suggestions.id", ondelete="CASCADE"), primary_key=True),
    Column("challenge_id", UUID(as_uuid=True), ForeignKey("challenges.id", ondelete="CASCADE"), primary_key=True),
)


class ResearchSuggestion(Base):
    __tablename__ = "research_suggestions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(255), nullable=False)
    deskripsi = Column(Text, nullable=True)

    status = Column(String(50), default="NEW", nullable=False)  # NEW, REVIEWED, ARCHIVED
    admin_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    personas = relationship("Persona", secondary=suggestion_personas, back_populates="suggestions")
    challenges = relationship("Challenge", secondary=suggestion_challenges, back_populates="suggestions")

    @property
    def persona_ids(self) -> List[uuid.UUID]:
        return [p.id for p in self.personas] if self.personas else []

    @property
    def challange_ids(self) -> List[uuid.UUID]:
        return [c.id for c in self.challenges] if self.challenges else []

    @property
    def challenge_ids(self) -> List[uuid.UUID]:
        return self.challange_ids

    # Compatibility properties for CMS & Admin
    @property
    def topic_wanted(self):
        return self.title

    @property
    def feedback(self):
        return self.deskripsi

    @property
    def persona_id(self):
        return self.personas[0].id if self.personas else None

    @property
    def persona_name(self):
        return ", ".join(p.name for p in self.personas) if self.personas else None

    @property
    def challenge_id(self):
        return self.challenges[0].id if self.challenges else None

    @property
    def challenge_name(self):
        return ", ".join(c.name for c in self.challenges) if self.challenges else None

    @property
    def zone_id(self):
        return self.challenge_id

    @property
    def zone_name(self):
        return self.challenge_name

    @property
    def visitor_name(self):
        return None

    @property
    def age_range(self):
        return None

    @property
    def screen_context(self):
        return "Explore"
