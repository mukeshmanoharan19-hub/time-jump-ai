import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    microsoft_oid = mapped_column(String(64), unique=True, index=True, nullable=False)
    email = mapped_column(String(320), nullable=True)
    display_name = mapped_column(String(256), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())

    sessions = relationship("AppSession", back_populates="user")


class AppSession(Base):
    __tablename__ = "app_sessions"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    token_hash = mapped_column(String(64), unique=True, index=True, nullable=False)
    graph_access_token = mapped_column(Text, nullable=False)
    graph_token_expires_at = mapped_column(DateTime(timezone=True), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at = mapped_column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="sessions")
