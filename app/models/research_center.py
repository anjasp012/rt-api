from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class ResearchCenter(Base):
    __tablename__ = "research_centers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    or_name = Column(String(255), nullable=True)
    code = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    innovations = relationship("Innovation", back_populates="research_center")
