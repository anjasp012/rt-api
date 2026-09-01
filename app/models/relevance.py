from sqlalchemy import Column, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base


class InnovationPersonaRelevance(Base):
    __tablename__ = "innovation_persona_relevance"

    id = Column(Integer, primary_key=True, index=True)
    innovation_id = Column(Integer, ForeignKey("innovations.id", ondelete="CASCADE"), nullable=False, index=True)
    persona_id = Column(Integer, ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, index=True)
    relevance_score = Column(Integer, default=50, nullable=False)
    custom_impact = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("innovation_id", "persona_id", name="uq_innovation_persona"),
    )

    innovation = relationship("Innovation", back_populates="persona_relevances")
    persona = relationship("Persona", back_populates="relevance_mappings")
