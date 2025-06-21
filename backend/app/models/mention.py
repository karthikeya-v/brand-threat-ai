from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, func, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.database import Base


class Mention(Base):
    __tablename__ = "mentions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), nullable=False)
    platform_id = Column(String(255))
    url = Column(Text)
    title = Column(Text)
    content = Column(Text, nullable=False)
    author = Column(String(255))
    author_followers = Column(Integer, default=0)
    engagement_count = Column(Integer, default=0)
    published_at = Column(DateTime(timezone=True))
    collected_at = Column(DateTime(timezone=True), server_default=func.now())
    processed = Column(Boolean, default=False)

    # Relationships
    brand = relationship("Brand", back_populates="mentions")
    threats = relationship("Threat", back_populates="mention", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_mentions_brand_processed_published', 'brand_id', 'processed', 'published_at'),
    )