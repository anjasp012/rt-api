from sqlalchemy import Column, Integer, String, JSON, DateTime, func
from app.db.session import Base


class TelemetryLog(Base):
    __tablename__ = "telemetry_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), index=True, nullable=False)
    persona_slug = Column(String(100), nullable=True)
    zone_slug = Column(String(100), nullable=True)
    innovation_slug = Column(String(255), nullable=True)
    metadata_payload = Column(JSON, default=dict, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
