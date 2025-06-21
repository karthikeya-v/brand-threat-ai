from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.db.database import get_db
from app.core.auth import get_current_active_user
from app.models.user import User
from app.models.brand import Brand
from app.models.mention import Mention

router = APIRouter()


class MentionResponse(BaseModel):
    id: str
    brand_id: str
    brand_name: str
    platform: str
    platform_id: Optional[str]
    url: Optional[str]
    title: Optional[str]
    content: str
    author: Optional[str]
    author_followers: int
    engagement_count: int
    published_at: Optional[str]
    collected_at: str
    processed: bool

    class Config:
        from_attributes = True


class PlatformStatus(BaseModel):
    platform: str
    status: str
    last_collection: Optional[str]
    mentions_collected: int
    errors: List[str]


@router.get("/", response_model=List[MentionResponse])
async def get_mentions(
    brand_id: Optional[UUID] = Query(None),
    platform: Optional[str] = Query(None),
    days: int = Query(7),
    limit: int = Query(100, le=500),
    processed: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # Build query
    query = select(Mention).options(selectinload(Mention.brand))
    
    # Filter by user's brands
    query = query.join(Brand).where(Brand.user_id == current_user.id)
    
    # Additional filters
    if brand_id:
        query = query.where(Mention.brand_id == brand_id)
    
    if platform:
        query = query.where(Mention.platform == platform)
    
    if processed is not None:
        query = query.where(Mention.processed == processed)
    
    # Date filter
    if days:
        since_date = datetime.utcnow() - timedelta(days=days)
        query = query.where(Mention.collected_at >= since_date)
    
    # Order and limit
    query = query.order_by(desc(Mention.collected_at)).limit(limit)
    
    result = await db.execute(query)
    mentions = result.scalars().all()
    
    mention_responses = []
    for mention in mentions:
        mention_responses.append(MentionResponse(
            id=str(mention.id),
            brand_id=str(mention.brand_id),
            brand_name=mention.brand.name,
            platform=mention.platform,
            platform_id=mention.platform_id,
            url=mention.url,
            title=mention.title,
            content=mention.content,
            author=mention.author,
            author_followers=mention.author_followers or 0,
            engagement_count=mention.engagement_count or 0,
            published_at=mention.published_at.isoformat() if mention.published_at else None,
            collected_at=mention.collected_at.isoformat(),
            processed=mention.processed
        ))
    
    return mention_responses


@router.post("/collect")
async def trigger_collection(
    brand_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Trigger manual data collection for brands"""
    
    if brand_id:
        # Verify brand ownership
        result = await db.execute(
            select(Brand).where(and_(Brand.id == brand_id, Brand.user_id == current_user.id))
        )
        brand = result.scalar_one_or_none()
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Trigger collection for specific brand
        # In real implementation, this would queue Celery tasks
        return {
            "message": f"Collection triggered for brand: {brand.name}",
            "brand_id": str(brand_id),
            "status": "queued"
        }
    else:
        # Trigger collection for all user's brands
        result = await db.execute(
            select(Brand).where(Brand.user_id == current_user.id)
        )
        brands = result.scalars().all()
        
        return {
            "message": f"Collection triggered for {len(brands)} brands",
            "brands": [{"id": str(b.id), "name": b.name} for b in brands],
            "status": "queued"
        }


@router.get("/platforms/status", response_model=List[PlatformStatus])
async def get_platform_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Check platform API status for user's brands"""
    
    # Get user's brands
    result = await db.execute(
        select(Brand).where(Brand.user_id == current_user.id)
    )
    brands = result.scalars().all()
    
    if not brands:
        return []
    
    # Get recent mentions by platform
    since_date = datetime.utcnow() - timedelta(hours=24)
    
    platform_stats = {}
    for brand in brands:
        brand_mentions = await db.execute(
            select(Mention)
            .where(and_(
                Mention.brand_id == brand.id,
                Mention.collected_at >= since_date
            ))
        )
        
        for mention in brand_mentions.scalars():
            platform = mention.platform
            if platform not in platform_stats:
                platform_stats[platform] = {
                    "mentions": [],
                    "errors": []
                }
            platform_stats[platform]["mentions"].append(mention)
    
    # Build status response
    status_list = []
    for platform, stats in platform_stats.items():
        last_mention = max(stats["mentions"], key=lambda m: m.collected_at) if stats["mentions"] else None
        
        status_list.append(PlatformStatus(
            platform=platform,
            status="active" if stats["mentions"] else "inactive",
            last_collection=last_mention.collected_at.isoformat() if last_mention else None,
            mentions_collected=len(stats["mentions"]),
            errors=stats["errors"]
        ))
    
    # Add default platforms if not present
    default_platforms = ["twitter", "reddit", "news", "youtube"]
    existing_platforms = {s.platform for s in status_list}
    
    for platform in default_platforms:
        if platform not in existing_platforms:
            status_list.append(PlatformStatus(
                platform=platform,
                status="not_configured",
                last_collection=None,
                mentions_collected=0,
                errors=[]
            ))
    
    return status_list


@router.get("/{mention_id}", response_model=MentionResponse)
async def get_mention(
    mention_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Mention)
        .options(selectinload(Mention.brand))
        .join(Brand)
        .where(and_(Mention.id == mention_id, Brand.user_id == current_user.id))
    )
    mention = result.scalar_one_or_none()
    
    if not mention:
        raise HTTPException(status_code=404, detail="Mention not found")
    
    return MentionResponse(
        id=str(mention.id),
        brand_id=str(mention.brand_id),
        brand_name=mention.brand.name,
        platform=mention.platform,
        platform_id=mention.platform_id,
        url=mention.url,
        title=mention.title,
        content=mention.content,
        author=mention.author,
        author_followers=mention.author_followers or 0,
        engagement_count=mention.engagement_count or 0,
        published_at=mention.published_at.isoformat() if mention.published_at else None,
        collected_at=mention.collected_at.isoformat(),
        processed=mention.processed
    )