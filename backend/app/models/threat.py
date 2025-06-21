from sqlalchemy import Column, String, Boolean, DateTime, Float, Text, func, ForeignKey, Index, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.database import Base


class Threat(Base):
    __tablename__ = "threats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    mention_id = Column(UUID(as_uuid=True), ForeignKey("mentions.id", ondelete="CASCADE"), nullable=False)
    threat_type = Column(String(100), nullable=False)
    severity_score = Column(Float, nullable=False)
    viral_potential = Column(Float, nullable=False)
    sentiment_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    ai_refined = Column(Boolean, default=False)
    status = Column(String(50), default="new")
    summary = Column(Text)
    suggested_responses = Column(ARRAY(Text))
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    brand = relationship("Brand", back_populates="threats")
    mention = relationship("Mention", back_populates="threats")
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_threats")
    alerts = relationship("Alert", back_populates="threat", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_threats_brand_status_severity_created', 'brand_id', 'status', 'severity_score', 'created_at'),
    )