from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    zone_number = Column(Integer, unique=True, index=True, nullable=False)
    name = Column(String(100), unique=True, index=True, nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    color_theme = Column(String(50), nullable=True)
    icon_name = Column(String(100), nullable=True)
    order_index = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    innovations = relationship("Innovation", back_populates="zone", cascade="all, delete-orphan")
    suggestions = relationship("ResearchSuggestion", back_populates="zone")
