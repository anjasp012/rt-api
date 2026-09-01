from sqlalchemy import Column, String, Text
from app.db.session import Base


class AppSetting(Base):
    __tablename__ = "app_settings"

    key = Column(String(50), primary_key=True, index=True)
    value = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
