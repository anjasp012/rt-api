import uuid
from sqlalchemy import Column, String, Integer, DateTime, func
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), default="Admin", nullable=False)
    role = Column(String(50), default="admin", nullable=False)  # superadmin / admin / user
    is_active = Column(Integer, default=1, nullable=False)      # 1: active, 0: inactive
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
