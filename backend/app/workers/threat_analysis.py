from celery import current_task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
import asyncio
import logging

from app.workers.celery_app import celery_app
from app.db.database import AsyncSessionLocal
from app.models.brand import Brand
from app.models.mention import Mention
from app.models.threat import Threat
from app.services.threat_analyzer import ThreatAnalyzer
from app.services.ai_refiner import AIRefiner

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def analyze_mention(self, mention_id: str):
    """Analyze a specific mention for threats"""
    try:
        return asyncio.run(_analyze_mention_async(mention_id))
    except Exception as e:
        logger.error(f"Error in analyze_mention: {str(e)}")
        self.retry(countdown=60, max_retries=3)


async def _analyze_mention_async(mention_id: str):
    """Async implementation of mention analysis"""
    async with AsyncSessionLocal() as db:
        try:
            # Get mention with brand
            result = await db.execute(
                select(Mention)
                .options(selectinload(Mention.brand))
                .where(Mention.id == mention_id)
            )
            mention = result.scalar_one_or_none()
            
            if not mention:
                return {"status": "error", "message": "Mention not found"}
            
            if mention.processed:
                return {"status": "skipped", "message": "Mention already processed"}
            
            # Initialize analyzers
            threat_analyzer = ThreatAnalyzer()
            ai_refiner = AIRefiner()
            
            # Perform initial analysis
            analysis = threat_analyzer.analyze_mention(mention, mention.brand)
            
            # Check if AI refinement is needed
            if threat_analyzer.needs_ai_refinement(analysis, mention):
                logger.info(f"Refining analysis with AI for mention {mention_id}")
                analysis = await ai_refiner.refine_threat_analysis(mention, mention.brand, analysis)
            
            # Generate response suggestions if not already provided
            if not analysis.suggested_responses:
                analysis.suggested_responses = threat_analyzer.generate_response_suggestions(
                    analysis, mention, mention.brand
                )
            
            # Create threat record if severity is above threshold
            if analysis.severity_score > 0.3:  # Configurable threshold
                threat = Threat(
                    brand_id=mention.brand_id,
                    mention_id=mention.id,
                    threat_type=analysis.threat_type,
                    severity_score=analysis.severity_score,
                    viral_potential=analysis.viral_potential,
                    sentiment_score=analysis.sentiment_score,
                    confidence=analysis.confidence,
                    ai_refined=analysis.ai_refined,
                    summary=analysis.summary,
                    suggested_responses=analysis.suggested_responses
                )
                
                db.add(threat)
                
                # Trigger alert if high severity
                if analysis.severity_score > 0.7:
                    # Queue alert notification
                    from app.workers.notifications import send_threat_alert
                    send_threat_alert.delay(str(threat.id))
            
            # Mark mention as processed
            mention.processed = True
            await db.commit()
            
            return {
                "status": "completed",
                "mention_id": mention_id,
                "threat_created": analysis.severity_score > 0.3,
                "severity_score": analysis.severity_score,
                "threat_type": analysis.threat_type,
                "ai_refined": analysis.ai_refined
            }
            
        except Exception as e:
            logger.error(f"Error in _analyze_mention_async: {str(e)}")
            raise


@celery_app.task(bind=True)
def analyze_unprocessed_mentions(self, brand_id: str = None, limit: int = 100):
    """Analyze unprocessed mentions"""
    try:
        return asyncio.run(_analyze_unprocessed_mentions_async(brand_id, limit))
    except Exception as e:
        logger.error(f"Error in analyze_unprocessed_mentions: {str(e)}")
        self.retry(countdown=120, max_retries=2)


async def _analyze_unprocessed_mentions_async(brand_id: str = None, limit: int = 100):
    """Async implementation of batch mention analysis"""
    async with AsyncSessionLocal() as db:
        try:
            # Build query for unprocessed mentions
            query = select(Mention).options(selectinload(Mention.brand)).where(
                Mention.processed == False
            )
            
            if brand_id:
                query = query.where(Mention.brand_id == brand_id)
            
            # Order by collected_at and limit
            query = query.order_by(Mention.collected_at.desc()).limit(limit)
            
            result = await db.execute(query)
            mentions = result.scalars().all()
            
            if not mentions:
                return {"status": "no_mentions", "message": "No unprocessed mentions found"}
            
            # Initialize analyzers
            threat_analyzer = ThreatAnalyzer()
            ai_refiner = AIRefiner()
            
            processed_count = 0
            threats_created = 0
            ai_refined_count = 0
            
            for mention in mentions:
                try:
                    # Skip if brand is inactive
                    if not mention.brand.is_active:
                        mention.processed = True
                        continue
                    
                    # Perform analysis
                    analysis = threat_analyzer.analyze_mention(mention, mention.brand)
                    
                    # Check for AI refinement
                    needs_ai = threat_analyzer.needs_ai_refinement(analysis, mention)
                    if needs_ai:
                        analysis = await ai_refiner.refine_threat_analysis(mention, mention.brand, analysis)
                        ai_refined_count += 1
                    
                    # Generate response suggestions
                    if not analysis.suggested_responses:
                        analysis.suggested_responses = threat_analyzer.generate_response_suggestions(
                            analysis, mention, mention.brand
                        )
                    
                    # Create threat if needed
                    if analysis.severity_score > 0.3:
                        threat = Threat(
                            brand_id=mention.brand_id,
                            mention_id=mention.id,
                            threat_type=analysis.threat_type,
                            severity_score=analysis.severity_score,
                            viral_potential=analysis.viral_potential,
                            sentiment_score=analysis.sentiment_score,
                            confidence=analysis.confidence,
                            ai_refined=analysis.ai_refined,
                            summary=analysis.summary,
                            suggested_responses=analysis.suggested_responses
                        )
                        
                        db.add(threat)
                        threats_created += 1
                        
                        # Queue high-severity alerts
                        if analysis.severity_score > 0.7:
                            from app.workers.notifications import send_threat_alert
                            send_threat_alert.delay(str(threat.id))
                    
                    # Mark as processed
                    mention.processed = True
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error analyzing mention {mention.id}: {str(e)}")
                    continue
            
            await db.commit()
            
            return {
                "status": "completed",
                "processed_mentions": processed_count,
                "threats_created": threats_created,
                "ai_refined": ai_refined_count,
                "total_mentions": len(mentions)
            }
            
        except Exception as e:
            logger.error(f"Error in _analyze_unprocessed_mentions_async: {str(e)}")
            raise


@celery_app.task(bind=True)
def analyze_brand_mentions(self, brand_id: str):
    """Analyze all unprocessed mentions for a specific brand"""
    try:
        return asyncio.run(_analyze_unprocessed_mentions_async(brand_id, limit=500))
    except Exception as e:
        logger.error(f"Error in analyze_brand_mentions: {str(e)}")
        self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True)
def reanalyze_threat(self, threat_id: str, force_ai: bool = False):
    """Re-analyze an existing threat, optionally forcing AI refinement"""
    try:
        return asyncio.run(_reanalyze_threat_async(threat_id, force_ai))
    except Exception as e:
        logger.error(f"Error in reanalyze_threat: {str(e)}")
        self.retry(countdown=60, max_retries=2)


async def _reanalyze_threat_async(threat_id: str, force_ai: bool = False):
    """Async implementation of threat re-analysis"""
    async with AsyncSessionLocal() as db:
        try:
            # Get threat with mention and brand
            result = await db.execute(
                select(Threat)
                .options(
                    selectinload(Threat.mention),
                    selectinload(Threat.brand)
                )
                .where(Threat.id == threat_id)
            )
            threat = result.scalar_one_or_none()
            
            if not threat:
                return {"status": "error", "message": "Threat not found"}
            
            # Initialize analyzers
            threat_analyzer = ThreatAnalyzer()
            ai_refiner = AIRefiner()
            
            # Perform fresh analysis
            analysis = threat_analyzer.analyze_mention(threat.mention, threat.brand)
            
            # Check for AI refinement
            needs_ai = force_ai or threat_analyzer.needs_ai_refinement(analysis, threat.mention)
            if needs_ai:
                analysis = await ai_refiner.refine_threat_analysis(
                    threat.mention, threat.brand, analysis
                )
            
            # Generate new response suggestions
            analysis.suggested_responses = threat_analyzer.generate_response_suggestions(
                analysis, threat.mention, threat.brand
            )
            
            # Update threat
            threat.threat_type = analysis.threat_type
            threat.severity_score = analysis.severity_score
            threat.viral_potential = analysis.viral_potential
            threat.sentiment_score = analysis.sentiment_score
            threat.confidence = analysis.confidence
            threat.ai_refined = analysis.ai_refined
            threat.summary = analysis.summary
            threat.suggested_responses = analysis.suggested_responses
            
            await db.commit()
            
            return {
                "status": "completed",
                "threat_id": threat_id,
                "severity_score": analysis.severity_score,
                "threat_type": analysis.threat_type,
                "ai_refined": analysis.ai_refined
            }
            
        except Exception as e:
            logger.error(f"Error in _reanalyze_threat_async: {str(e)}")
            raise


@celery_app.task(bind=True)
def analyze_trending_context(self, brand_id: str, hours_back: int = 24):
    """Analyze trending context for a brand's recent mentions"""
    try:
        return asyncio.run(_analyze_trending_context_async(brand_id, hours_back))
    except Exception as e:
        logger.error(f"Error in analyze_trending_context: {str(e)}")
        self.retry(countdown=180, max_retries=2)


async def _analyze_trending_context_async(brand_id: str, hours_back: int = 24):
    """Async implementation of trending context analysis"""
    async with AsyncSessionLocal() as db:
        try:
            from datetime import datetime, timedelta
            
            # Get recent mentions for the brand
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            result = await db.execute(
                select(Mention)
                .options(selectinload(Mention.brand))
                .where(and_(
                    Mention.brand_id == brand_id,
                    Mention.collected_at >= cutoff_time
                ))
                .order_by(Mention.collected_at.desc())
                .limit(50)
            )
            mentions = result.scalars().all()
            
            if len(mentions) < 3:
                return {"status": "insufficient_data", "mentions_count": len(mentions)}
            
            # Get brand
            brand = mentions[0].brand if mentions else None
            if not brand:
                return {"status": "error", "message": "Brand not found"}
            
            # Use AI to analyze trending context
            ai_refiner = AIRefiner()
            trend_analysis = await ai_refiner.analyze_trend_context(mentions, brand)
            
            return {
                "status": "completed",
                "brand_id": brand_id,
                "brand_name": brand.name,
                "mentions_analyzed": len(mentions),
                "trend_analysis": trend_analysis,
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in _analyze_trending_context_async: {str(e)}")
            raise


# Utility functions for manual triggering
def trigger_mention_analysis(mention_id: str):
    """Trigger analysis for a specific mention"""
    return analyze_mention.delay(mention_id)


def trigger_brand_analysis(brand_id: str):
    """Trigger analysis for all mentions of a brand"""
    return analyze_brand_mentions.delay(brand_id)


def trigger_batch_analysis(limit: int = 100):
    """Trigger batch analysis of unprocessed mentions"""
    return analyze_unprocessed_mentions.delay(limit=limit)