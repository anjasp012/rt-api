import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class ModuleInteractionLog(Base):
    __tablename__ = "module_interaction_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("personas.id", ondelete="SET NULL"), nullable=True, index=True)
    challenge_id = Column(UUID(as_uuid=True), ForeignKey("challenges.id", ondelete="SET NULL"), nullable=True, index=True)
    solution_id = Column(UUID(as_uuid=True), ForeignKey("solutions.id", ondelete="SET NULL"), nullable=True, index=True)
    event = Column(String(50), default="EXPLORE", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    persona = relationship("Persona")
    challenge = relationship("Challenge")
    solution = relationship("Solution")

    @property
    def zone_id(self):
        return self.challenge_id

    @property
    def persona_name(self):
        return self.persona.name if self.persona else None

    @property
    def challenge_name(self):
        return self.challenge.name if self.challenge else None

    @property
    def zone_name(self):
        return self.challenge_name

    @property
    def solution_title(self):
        return self.solution.title if self.solution else None

    @property
    def innovation_title(self):
        return self.solution_title
