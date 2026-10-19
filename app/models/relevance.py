import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base


class SolutionPersonaRelevance(Base):
    __tablename__ = "solution_persona_relevances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    solution_id = Column(UUID(as_uuid=True), ForeignKey("solutions.id", ondelete="CASCADE"), nullable=False, index=True)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, index=True)
    relevance_score = Column(Integer, default=50, nullable=False)
    custom_impact = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("solution_id", "persona_id", name="uq_solution_persona"),
    )

    solution = relationship("Solution", back_populates="persona_relevances")
    persona = relationship("Persona", back_populates="relevance_mappings")

    # Backward compatibility properties
    @property
    def innovation_id(self):
        return self.solution_id

    @property
    def innovation(self):
        return self.solution


InnovationPersonaRelevance = SolutionPersonaRelevance
