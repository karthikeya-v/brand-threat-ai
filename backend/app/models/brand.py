from sqlalchemy import Column, String, Boolean, DateTime, Float, func, ForeignKey, ARRAY, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.database import Base


class Brand(Base):
    __tablename__ = "brands"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    keywords = Column(ARRAY(Text), nullable=False)
    competitors = Column(ARRAY(Text))
    industry = Column(String(100))
    sentiment_threshold = Column(Float, default=-0.4)
    viral_threshold = Column(Float, default=0.7)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="brands")
    mentions = relationship("Mention", back_populates="brand", cascade="all, delete-orphan")
    threats = relationship("Threat", back_populates="brand", cascade="all, delete-orphan")