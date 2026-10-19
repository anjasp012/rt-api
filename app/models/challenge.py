import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, Boolean, Text, DateTime, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(150), unique=True, index=True, nullable=False)
    slug = Column(String(150), unique=True, index=True, nullable=False)
    color = Column(String(50), nullable=True)        # Warna bidang / tantangan (e.g. "#996A12")
    icon = Column(String(100), nullable=True)        # Ikon tantangan (e.g. "rice", "cow")
    description = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Solusi yang Tantangan Utamanya adalah Challenge ini
    solutions = relationship(
        "Solution",
        foreign_keys="[Solution.challenge_id]",
        back_populates="challenge",
        cascade="all, delete-orphan"
    )

    # Solusi yang memiliki Tantangan ini sebagai Tantangan Relevan (M2M)
    relevant_solutions = relationship(
        "Solution",
        secondary="solution_relevant_challenges",
        back_populates="relevant_challenges"
    )

    suggestions = relationship("ResearchSuggestion", secondary="suggestion_challenges", back_populates="challenges")

    # Backward compatibility aliases
    @property
    def innovations(self):
        return self.solutions

    @property
    def relevant_innovations(self):
        return self.relevant_solutions


# Alias kelas untuk backward compatibility
Zone = Challenge
