from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.db.database import get_db
from app.core.auth import get_current_active_user
from app.models.user import User
from app.models.brand import Brand
from app.models.threat import Threat
from app.models.mention import Mention

router = APIRouter()


class ThreatResponse(BaseModel):
    id: str
    brand_id: str
    brand_name: str
    mention_id: str
    threat_type: str
    severity_score: float
    viral_potential: float
    sentiment_score: float
    confidence: float
    ai_refined: bool
    status: str
    summary: Optional[str]
    suggested_responses: List[str]
    assigned_to: Optional[str]
    created_at: str
    updated_at: str
    mention: dict

    class Config:
        from_attributes = True


class ThreatUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[UUID] = None


class ThreatStats(BaseModel):
    total_threats: int
    new_threats: int
    in_progress_threats: int
    resolved_threats: int
    high_severity_count: int
    avg_severity: float


@router.get("/", response_model=List[ThreatResponse])
async def get_threats(
    brand_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    severity_min: Optional[float] = Query(None),
    days: Optional[int] = Query(7),
    limit: int = Query(50, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # Build query
    query = select(Threat).options(
        selectinload(Threat.brand),
        selectinload(Threat.mention),
        selectinload(Threat.assignee)
    )
    
    # Filter by user's brands
    query = query.join(Brand).where(Brand.user_id == current_user.id)
    
    # Additional filters
    if brand_id:
        query = query.where(Threat.brand_id == brand_id)
    
    if status:
        query = query.where(Threat.status == status)
    
    if severity_min:
        query = query.where(Threat.severity_score >= severity_min)
    
    if days:
        since_date = datetime.utcnow() - timedelta(days=days)
        query = query.where(Threat.created_at >= since_date)
    
    # Order and limit
    query = query.order_by(desc(Threat.severity_score), desc(Threat.created_at)).limit(limit)
    
    result = await db.execute(query)
    threats = result.scalars().all()
    
    threat_responses = []
    for threat in threats:
        mention_data = {
            "id": str(threat.mention.id),
            "platform": threat.mention.platform,
            "content": threat.mention.content,
            "author": threat.mention.author,
            "author_followers": threat.mention.author_followers,
            "engagement_count": threat.mention.engagement_count,
            "url": threat.mention.url,
            "published_at": threat.mention.published_at.isoformat() if threat.mention.published_at else None
        }
        
        threat_responses.append(ThreatResponse(
            id=str(threat.id),
            brand_id=str(threat.brand_id),
            brand_name=threat.brand.name,
            mention_id=str(threat.mention_id),
            threat_type=threat.threat_type,
            severity_score=threat.severity_score,
            viral_potential=threat.viral_potential,
            sentiment_score=threat.sentiment_score,
            confidence=threat.confidence,
            ai_refined=threat.ai_refined,
            status=threat.status,
            summary=threat.summary,
            suggested_responses=threat.suggested_responses or [],
            assigned_to=str(threat.assigned_to) if threat.assigned_to else None,
            created_at=threat.created_at.isoformat(),
            updated_at=threat.updated_at.isoformat(),
            mention=mention_data
        ))
    
    return threat_responses


@router.get("/stats", response_model=ThreatStats)
async def get_threat_stats(
    brand_id: Optional[UUID] = Query(None),
    days: int = Query(30),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # Base query
    query = select(Threat).join(Brand).where(Brand.user_id == current_user.id)
    
    if brand_id:
        query = query.where(Threat.brand_id == brand_id)
    
    if days:
        since_date = datetime.utcnow() - timedelta(days=days)
        query = query.where(Threat.created_at >= since_date)
    
    result = await db.execute(query)
    threats = result.scalars().all()
    
    if not threats:
        return ThreatStats(
            total_threats=0,
            new_threats=0,
            in_progress_threats=0,
            resolved_threats=0,
            high_severity_count=0,
            avg_severity=0.0
        )
    
    # Calculate stats
    total_threats = len(threats)
    new_threats = len([t for t in threats if t.status == "new"])
    in_progress_threats = len([t for t in threats if t.status == "reviewing"])
    resolved_threats = len([t for t in threats if t.status in ["resolved", "dismissed"]])
    high_severity_count = len([t for t in threats if t.severity_score > 0.7])
    avg_severity = sum([t.severity_score for t in threats]) / total_threats
    
    return ThreatStats(
        total_threats=total_threats,
        new_threats=new_threats,
        in_progress_threats=in_progress_threats,
        resolved_threats=resolved_threats,
        high_severity_count=high_severity_count,
        avg_severity=avg_severity
    )


@router.get("/{threat_id}", response_model=ThreatResponse)
async def get_threat(
    threat_id: UUID,
    current_user: User = Depends(get_current_active_user),  
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Threat)
        .options(
            selectinload(Threat.brand),
            selectinload(Threat.mention),
            selectinload(Threat.assignee)
        )
        .join(Brand)
        .where(and_(Threat.id == threat_id, Brand.user_id == current_user.id))
    )
    threat = result.scalar_one_or_none()
    
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")
    
    mention_data = {
        "id": str(threat.mention.id),
        "platform": threat.mention.platform,
        "content": threat.mention.content,
        "author": threat.mention.author,
        "author_followers": threat.mention.author_followers,
        "engagement_count": threat.mention.engagement_count,
        "url": threat.mention.url,
        "published_at": threat.mention.published_at.isoformat() if threat.mention.published_at else None
    }
    
    return ThreatResponse(
        id=str(threat.id),
        brand_id=str(threat.brand_id),
        brand_name=threat.brand.name,
        mention_id=str(threat.mention_id),
        threat_type=threat.threat_type,
        severity_score=threat.severity_score,
        viral_potential=threat.viral_potential,
        sentiment_score=threat.sentiment_score,
        confidence=threat.confidence,
        ai_refined=threat.ai_refined,
        status=threat.status,
        summary=threat.summary,
        suggested_responses=threat.suggested_responses or [],
        assigned_to=str(threat.assigned_to) if threat.assigned_to else None,
        created_at=threat.created_at.isoformat(),
        updated_at=threat.updated_at.isoformat(),
        mention=mention_data
    )


@router.put("/{threat_id}/status")
async def update_threat_status(
    threat_id: UUID,
    update_data: ThreatUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Threat)
        .join(Brand)
        .where(and_(Threat.id == threat_id, Brand.user_id == current_user.id))
    )
    threat = result.scalar_one_or_none()
    
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")
    
    # Update fields
    if update_data.status:
        if update_data.status not in ["new", "reviewing", "resolved", "dismissed"]:
            raise HTTPException(status_code=400, detail="Invalid status")
        threat.status = update_data.status
    
    if update_data.assigned_to:
        # Verify assignee is part of the user's organization (simplified for now)
        threat.assigned_to = update_data.assigned_to
    
    await db.commit()
    await db.refresh(threat)
    
    return {"message": "Threat updated successfully", "status": threat.status}


@router.post("/{threat_id}/response")
async def submit_threat_response(
    threat_id: UUID,
    response_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Threat)
        .join(Brand)
        .where(and_(Threat.id == threat_id, Brand.user_id == current_user.id))
    )
    threat = result.scalar_one_or_none()
    
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")
    
    # This would integrate with platform APIs to post responses
    # For now, just log the response action
    response_action = response_data.get("action")
    response_message = response_data.get("message", "")
    
    # Update threat status to resolved if response was successful
    threat.status = "resolved"
    await db.commit()
    
    return {
        "message": "Response submitted successfully",
        "action": response_action,
        "threat_id": str(threat_id)
    }


@router.put("/{threat_id}/assign")
async def assign_threat(
    threat_id: UUID,
    assignee_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Threat)
        .join(Brand)
        .where(and_(Threat.id == threat_id, Brand.user_id == current_user.id))
    )
    threat = result.scalar_one_or_none()
    
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")
    
    assignee_id = assignee_data.get("user_id")
    if assignee_id:
        threat.assigned_to = UUID(assignee_id)
        threat.status = "reviewing"
    else:
        threat.assigned_to = None
    
    await db.commit()
    
    return {
        "message": "Threat assignment updated",
        "assigned_to": str(assignee_id) if assignee_id else None
    }