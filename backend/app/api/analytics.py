from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel
from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime, timedelta

from app.db.database import get_db
from app.api.keycloak_auth import get_current_keycloak_user
from app.models.user import User
from app.models.brand import Brand
from app.models.threat import Threat
from app.models.mention import Mention


async def get_or_create_user_from_keycloak(keycloak_user: dict, db: AsyncSession) -> User:
    """Get or create user from Keycloak user data"""
    user_id = keycloak_user.get("sub")
    email = keycloak_user.get("email")
    
    # Try to find existing user by Keycloak sub (user_id)
    result = await db.execute(
        select(User).where(User.keycloak_id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user:
        return user
    
    # Try to find by email if no keycloak_id match
    if email:
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Update the user with Keycloak ID
            user.keycloak_id = user_id
            await db.commit()
            return user
    
    # Create new user
    user = User(
        keycloak_id=user_id,
        email=email,
        name=keycloak_user.get("name", keycloak_user.get("preferred_username", "")),
        tier="starter",  # Default tier for new users
        is_active=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

router = APIRouter()


class OverviewStats(BaseModel):
    total_brands: int
    total_mentions: int
    total_threats: int
    high_severity_threats: int
    avg_sentiment: float
    threat_resolution_rate: float


class SentimentTrend(BaseModel):
    date: str
    avg_sentiment: float
    mention_count: int
    threat_count: int


class ThreatBreakdown(BaseModel):
    threat_type: str
    count: int
    avg_severity: float
    percentage: float


class PlatformPerformance(BaseModel):
    platform: str
    mention_count: int
    threat_count: int
    avg_sentiment: float
    engagement_rate: float


@router.get("/overview", response_model=OverviewStats)
async def get_overview_stats(
    brand_id: Optional[UUID] = Query(None),
    days: int = Query(30),
    keycloak_user: dict = Depends(get_current_keycloak_user),
    db: AsyncSession = Depends(get_db)
):
    current_user = await get_or_create_user_from_keycloak(keycloak_user, db)
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Base query for user's brands
    brand_query = select(Brand).where(Brand.user_id == current_user.id)
    if brand_id:
        brand_query = brand_query.where(Brand.id == brand_id)
    
    brands_result = await db.execute(brand_query)
    brands = brands_result.scalars().all()
    brand_ids = [brand.id for brand in brands]
    
    if not brand_ids:
        return OverviewStats(
            total_brands=0,
            total_mentions=0,
            total_threats=0,
            high_severity_threats=0,
            avg_sentiment=0.0,
            threat_resolution_rate=0.0
        )
    
    # Get mentions count
    mentions_result = await db.execute(
        select(func.count(Mention.id))
        .where(and_(
            Mention.brand_id.in_(brand_ids),
            Mention.collected_at >= since_date
        ))
    )
    total_mentions = mentions_result.scalar() or 0
    
    # Get threats data
    threats_result = await db.execute(
        select(Threat)
        .where(and_(
            Threat.brand_id.in_(brand_ids),
            Threat.created_at >= since_date
        ))
    )
    threats = threats_result.scalars().all()
    
    total_threats = len(threats)
    high_severity_threats = len([t for t in threats if t.severity_score > 0.7])
    avg_sentiment = sum([t.sentiment_score for t in threats]) / len(threats) if threats else 0.0
    
    resolved_threats = len([t for t in threats if t.status in ["resolved", "dismissed"]])
    threat_resolution_rate = (resolved_threats / total_threats * 100) if total_threats > 0 else 0.0
    
    return OverviewStats(
        total_brands=len(brands),
        total_mentions=total_mentions,
        total_threats=total_threats,
        high_severity_threats=high_severity_threats,
        avg_sentiment=avg_sentiment,
        threat_resolution_rate=threat_resolution_rate
    )


@router.get("/sentiment-trends", response_model=List[SentimentTrend])
async def get_sentiment_trends(
    brand_id: Optional[UUID] = Query(None),
    days: int = Query(30),
    keycloak_user: dict = Depends(get_current_keycloak_user),
    db: AsyncSession = Depends(get_db)
):
    current_user = await get_or_create_user_from_keycloak(keycloak_user, db)
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Get brand IDs
    brand_query = select(Brand).where(Brand.user_id == current_user.id)
    if brand_id:
        brand_query = brand_query.where(Brand.id == brand_id)
    
    brands_result = await db.execute(brand_query)
    brands = brands_result.scalars().all()
    brand_ids = [brand.id for brand in brands]
    
    if not brand_ids:
        return []
    
    # Get daily aggregated data
    threats_result = await db.execute(
        select(Threat)
        .where(and_(
            Threat.brand_id.in_(brand_ids),
            Threat.created_at >= since_date
        ))
        .order_by(Threat.created_at)
    )
    threats = threats_result.scalars().all()
    
    mentions_result = await db.execute(
        select(Mention)
        .where(and_(
            Mention.brand_id.in_(brand_ids),
            Mention.collected_at >= since_date
        ))
        .order_by(Mention.collected_at)
    )
    mentions = mentions_result.scalars().all()
    
    # Group by date
    daily_data = {}
    
    # Process threats
    for threat in threats:
        date_key = threat.created_at.date().isoformat()
        if date_key not in daily_data:
            daily_data[date_key] = {
                "sentiment_scores": [],
                "mention_count": 0,
                "threat_count": 0
            }
        daily_data[date_key]["sentiment_scores"].append(threat.sentiment_score)
        daily_data[date_key]["threat_count"] += 1
    
    # Process mentions
    for mention in mentions:
        date_key = mention.collected_at.date().isoformat()
        if date_key not in daily_data:
            daily_data[date_key] = {
                "sentiment_scores": [],
                "mention_count": 0,
                "threat_count": 0
            }
        daily_data[date_key]["mention_count"] += 1
    
    # Build response
    trends = []
    for date_str, data in sorted(daily_data.items()):
        avg_sentiment = sum(data["sentiment_scores"]) / len(data["sentiment_scores"]) if data["sentiment_scores"] else 0.0
        
        trends.append(SentimentTrend(
            date=date_str,
            avg_sentiment=avg_sentiment,
            mention_count=data["mention_count"],
            threat_count=data["threat_count"]
        ))
    
    return trends


@router.get("/threat-breakdown", response_model=List[ThreatBreakdown])
async def get_threat_breakdown(
    brand_id: Optional[UUID] = Query(None),
    days: int = Query(30),
    keycloak_user: dict = Depends(get_current_keycloak_user),
    db: AsyncSession = Depends(get_db)
):
    current_user = await get_or_create_user_from_keycloak(keycloak_user, db)
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Get brand IDs
    brand_query = select(Brand).where(Brand.user_id == current_user.id)
    if brand_id:
        brand_query = brand_query.where(Brand.id == brand_id)
    
    brands_result = await db.execute(brand_query)
    brands = brands_result.scalars().all()
    brand_ids = [brand.id for brand in brands]
    
    if not brand_ids:
        return []
    
    # Get threats
    threats_result = await db.execute(
        select(Threat)
        .where(and_(
            Threat.brand_id.in_(brand_ids),
            Threat.created_at >= since_date
        ))
    )
    threats = threats_result.scalars().all()
    
    if not threats:
        return []
    
    # Group by threat type
    threat_groups = {}
    total_threats = len(threats)
    
    for threat in threats:
        threat_type = threat.threat_type
        if threat_type not in threat_groups:
            threat_groups[threat_type] = {
                "count": 0,
                "severity_scores": []
            }
        threat_groups[threat_type]["count"] += 1
        threat_groups[threat_type]["severity_scores"].append(threat.severity_score)
    
    # Build response
    breakdown = []
    for threat_type, data in threat_groups.items():
        avg_severity = sum(data["severity_scores"]) / len(data["severity_scores"])
        percentage = (data["count"] / total_threats) * 100
        
        breakdown.append(ThreatBreakdown(
            threat_type=threat_type,
            count=data["count"],
            avg_severity=avg_severity,
            percentage=percentage
        ))
    
    return sorted(breakdown, key=lambda x: x.count, reverse=True)


@router.get("/platform-performance", response_model=List[PlatformPerformance])
async def get_platform_performance(
    brand_id: Optional[UUID] = Query(None),
    days: int = Query(30),
    keycloak_user: dict = Depends(get_current_keycloak_user),
    db: AsyncSession = Depends(get_db)
):
    current_user = await get_or_create_user_from_keycloak(keycloak_user, db)
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Get brand IDs
    brand_query = select(Brand).where(Brand.user_id == current_user.id)
    if brand_id:
        brand_query = brand_query.where(Brand.id == brand_id)
    
    brands_result = await db.execute(brand_query)
    brands = brands_result.scalars().all()
    brand_ids = [brand.id for brand in brands]
    
    if not brand_ids:
        return []
    
    # Get mentions and threats
    mentions_result = await db.execute(
        select(Mention)
        .where(and_(
            Mention.brand_id.in_(brand_ids),
            Mention.collected_at >= since_date
        ))
    )
    mentions = mentions_result.scalars().all()
    
    threats_result = await db.execute(
        select(Threat)
        .join(Mention)
        .where(and_(
            Threat.brand_id.in_(brand_ids),
            Threat.created_at >= since_date
        ))
    )
    threats = threats_result.scalars().all()
    
    # Group by platform
    platform_data = {}
    
    # Process mentions
    for mention in mentions:
        platform = mention.platform
        if platform not in platform_data:
            platform_data[platform] = {
                "mentions": [],
                "threats": [],
                "total_engagement": 0
            }
        platform_data[platform]["mentions"].append(mention)
        platform_data[platform]["total_engagement"] += mention.engagement_count or 0
    
    # Process threats
    for threat in threats:
        # Get the mention's platform through the relationship
        mention_result = await db.execute(
            select(Mention).where(Mention.id == threat.mention_id)
        )
        mention = mention_result.scalar_one_or_none()
        
        if mention:
            platform = mention.platform
            if platform in platform_data:
                platform_data[platform]["threats"].append(threat)
    
    # Build response
    performance = []
    for platform, data in platform_data.items():
        mention_count = len(data["mentions"])
        threat_count = len(data["threats"])
        
        # Calculate average sentiment from threats
        avg_sentiment = 0.0
        if data["threats"]:
            avg_sentiment = sum([t.sentiment_score for t in data["threats"]]) / len(data["threats"])
        
        # Calculate engagement rate
        total_mentions_with_engagement = sum(1 for m in data["mentions"] if m.engagement_count and m.engagement_count > 0)
        engagement_rate = (total_mentions_with_engagement / mention_count * 100) if mention_count > 0 else 0.0
        
        performance.append(PlatformPerformance(
            platform=platform,
            mention_count=mention_count,
            threat_count=threat_count,
            avg_sentiment=avg_sentiment,
            engagement_rate=engagement_rate
        ))
    
    return sorted(performance, key=lambda x: x.mention_count, reverse=True)