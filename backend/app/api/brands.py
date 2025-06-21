from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

from app.db.database import get_db
from app.core.auth import get_current_active_user
from app.models.user import User
from app.models.brand import Brand
from app.models.threat import Threat
from app.models.mention import Mention

router = APIRouter()


class BrandCreate(BaseModel):
    name: str
    keywords: List[str]
    competitors: Optional[List[str]] = []
    industry: Optional[str] = None
    sentiment_threshold: float = -0.4
    viral_threshold: float = 0.7


class BrandUpdate(BaseModel):
    name: Optional[str] = None
    keywords: Optional[List[str]] = None
    competitors: Optional[List[str]] = None
    industry: Optional[str] = None
    sentiment_threshold: Optional[float] = None
    viral_threshold: Optional[float] = None
    is_active: Optional[bool] = None


class BrandStats(BaseModel):
    total_mentions: int
    new_threats: int
    high_severity_threats: int
    avg_sentiment: float


class BrandResponse(BaseModel):
    id: str
    name: str
    keywords: List[str]
    competitors: List[str]
    industry: Optional[str]
    sentiment_threshold: float
    viral_threshold: float
    is_active: bool
    created_at: str
    stats: Optional[BrandStats] = None

    class Config:
        from_attributes = True


@router.get("/", response_model=List[BrandResponse])
async def get_brands(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # Get brands with stats
    result = await db.execute(
        select(Brand)
        .where(Brand.user_id == current_user.id)
        .options(selectinload(Brand.mentions), selectinload(Brand.threats))
        .order_by(desc(Brand.created_at))
    )
    brands = result.scalars().all()
    
    brand_responses = []
    for brand in brands:
        # Calculate stats
        total_mentions = len(brand.mentions)
        new_threats = len([t for t in brand.threats if t.status == "new"])
        high_severity_threats = len([t for t in brand.threats if t.severity_score > 0.7])
        avg_sentiment = sum([t.sentiment_score for t in brand.threats]) / len(brand.threats) if brand.threats else 0.0
        
        stats = BrandStats(
            total_mentions=total_mentions,
            new_threats=new_threats,
            high_severity_threats=high_severity_threats,
            avg_sentiment=avg_sentiment
        )
        
        brand_responses.append(BrandResponse(
            id=str(brand.id),
            name=brand.name,
            keywords=brand.keywords or [],
            competitors=brand.competitors or [],
            industry=brand.industry,
            sentiment_threshold=brand.sentiment_threshold,
            viral_threshold=brand.viral_threshold,
            is_active=brand.is_active,
            created_at=brand.created_at.isoformat(),
            stats=stats
        ))
    
    return brand_responses


@router.post("/", response_model=BrandResponse)
async def create_brand(
    brand_data: BrandCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # Check tier limits
    if current_user.tier == "starter":
        existing_brands = await db.execute(
            select(func.count(Brand.id)).where(Brand.user_id == current_user.id)
        )
        if existing_brands.scalar() >= 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Starter tier limited to 1 brand"
            )
    elif current_user.tier == "professional":
        existing_brands = await db.execute(
            select(func.count(Brand.id)).where(Brand.user_id == current_user.id)
        )
        if existing_brands.scalar() >= 5:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Professional tier limited to 5 brands"
            )
    
    brand = Brand(
        user_id=current_user.id,
        name=brand_data.name,
        keywords=brand_data.keywords,
        competitors=brand_data.competitors,
        industry=brand_data.industry,
        sentiment_threshold=brand_data.sentiment_threshold,
        viral_threshold=brand_data.viral_threshold
    )
    
    db.add(brand)
    await db.commit()
    await db.refresh(brand)
    
    return BrandResponse(
        id=str(brand.id),
        name=brand.name,
        keywords=brand.keywords or [],
        competitors=brand.competitors or [],
        industry=brand.industry,
        sentiment_threshold=brand.sentiment_threshold,
        viral_threshold=brand.viral_threshold,
        is_active=brand.is_active,
        created_at=brand.created_at.isoformat()
    )


@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand(
    brand_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Brand)
        .where(Brand.id == brand_id, Brand.user_id == current_user.id)
        .options(selectinload(Brand.mentions), selectinload(Brand.threats))
    )
    brand = result.scalar_one_or_none()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Calculate recent stats (last 7 days)
    from datetime import datetime, timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    recent_mentions = [m for m in brand.mentions if m.collected_at >= week_ago]
    recent_threats = [t for t in brand.threats if t.created_at >= week_ago]
    
    stats = BrandStats(
        total_mentions=len(recent_mentions),
        new_threats=len([t for t in recent_threats if t.status == "new"]),
        high_severity_threats=len([t for t in recent_threats if t.severity_score > 0.7]),
        avg_sentiment=sum([t.sentiment_score for t in recent_threats]) / len(recent_threats) if recent_threats else 0.0
    )
    
    return BrandResponse(
        id=str(brand.id),
        name=brand.name,
        keywords=brand.keywords or [],
        competitors=brand.competitors or [],
        industry=brand.industry,
        sentiment_threshold=brand.sentiment_threshold,
        viral_threshold=brand.viral_threshold,
        is_active=brand.is_active,
        created_at=brand.created_at.isoformat(),
        stats=stats
    )


@router.put("/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: UUID,
    brand_data: BrandUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Brand).where(Brand.id == brand_id, Brand.user_id == current_user.id)
    )
    brand = result.scalar_one_or_none()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Update fields
    update_data = brand_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(brand, field, value)
    
    await db.commit()
    await db.refresh(brand)
    
    return BrandResponse(
        id=str(brand.id),
        name=brand.name,
        keywords=brand.keywords or [],
        competitors=brand.competitors or [],
        industry=brand.industry,
        sentiment_threshold=brand.sentiment_threshold,
        viral_threshold=brand.viral_threshold,
        is_active=brand.is_active,
        created_at=brand.created_at.isoformat()
    )


@router.delete("/{brand_id}")
async def delete_brand(
    brand_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Brand).where(Brand.id == brand_id, Brand.user_id == current_user.id)
    )
    brand = result.scalar_one_or_none()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    await db.delete(brand)
    await db.commit()
    
    return {"message": "Brand deleted successfully"}


@router.post("/{brand_id}/test")
async def test_brand_monitoring(
    brand_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Brand).where(Brand.id == brand_id, Brand.user_id == current_user.id)
    )
    brand = result.scalar_one_or_none()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # This would trigger a test collection in a real implementation
    return {
        "message": "Test monitoring initiated",
        "brand": brand.name,
        "keywords": brand.keywords,
        "status": "monitoring_test_queued"
    }