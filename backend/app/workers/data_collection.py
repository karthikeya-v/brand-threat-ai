from celery import current_task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import asyncio
import logging

from app.workers.celery_app import celery_app
from app.db.database import AsyncSessionLocal
from app.models.brand import Brand
from app.models.mention import Mention
from app.services.collectors import TwitterCollector, RedditCollector, NewsCollector, YouTubeCollector

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def collect_brand_mentions(self, brand_id: str, hours_back: int = 24):
    """Collect mentions for a specific brand from all platforms"""
    try:
        # Run async function in sync context
        return asyncio.run(_collect_brand_mentions_async(brand_id, hours_back))
    except Exception as e:
        logger.error(f"Error in collect_brand_mentions: {str(e)}")
        self.retry(countdown=60, max_retries=3)


async def _collect_brand_mentions_async(brand_id: str, hours_back: int = 24):
    """Async implementation of brand mention collection"""
    async with AsyncSessionLocal() as db:
        try:
            # Get brand
            result = await db.execute(select(Brand).where(Brand.id == brand_id))
            brand = result.scalar_one_or_none()
            
            if not brand or not brand.is_active:
                return {"status": "skipped", "reason": "brand not found or inactive"}
            
            # Initialize collectors
            collectors = [
                TwitterCollector(),
                RedditCollector(), 
                NewsCollector(),
                YouTubeCollector()
            ]
            
            total_mentions = 0
            platform_results = {}
            
            # Collect from each platform
            for collector in collectors:
                try:
                    if not collector.is_configured():
                        platform_results[collector.platform_name] = {
                            "status": "not_configured",
                            "mentions": 0
                        }
                        continue
                    
                    mentions = await collector.safe_collect(brand, hours_back)
                    
                    # Save mentions to database
                    saved_count = 0
                    for mention_data in mentions:
                        # Check if mention already exists
                        existing = await db.execute(
                            select(Mention).where(
                                Mention.platform == mention_data["platform"],
                                Mention.platform_id == mention_data["platform_id"]
                            )
                        )
                        
                        if existing.scalar_one_or_none():
                            continue  # Skip duplicates
                        
                        # Create new mention
                        mention = Mention(**mention_data)
                        db.add(mention)
                        saved_count += 1
                    
                    await db.commit()
                    
                    platform_results[collector.platform_name] = {
                        "status": "success",
                        "mentions": saved_count
                    }
                    total_mentions += saved_count
                    
                    logger.info(f"Collected {saved_count} mentions from {collector.platform_name} for brand {brand.name}")
                    
                except Exception as e:
                    logger.error(f"Error collecting from {collector.platform_name}: {str(e)}")
                    platform_results[collector.platform_name] = {
                        "status": "error",
                        "error": str(e),
                        "mentions": 0
                    }
            
            return {
                "status": "completed",
                "brand_id": brand_id,
                "brand_name": brand.name,
                "total_mentions": total_mentions,
                "platforms": platform_results,
                "collected_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in _collect_brand_mentions_async: {str(e)}")
            raise


@celery_app.task(bind=True)
def collect_all_mentions(self):
    """Collect mentions for all active brands"""
    try:
        return asyncio.run(_collect_all_mentions_async())
    except Exception as e:
        logger.error(f"Error in collect_all_mentions: {str(e)}")
        self.retry(countdown=300, max_retries=2)


async def _collect_all_mentions_async():
    """Async implementation of collecting mentions for all brands"""
    async with AsyncSessionLocal() as db:
        try:
            # Get all active brands
            result = await db.execute(
                select(Brand).where(Brand.is_active == True)
            )
            brands = result.scalars().all()
            
            if not brands:
                return {"status": "no_brands", "message": "No active brands found"}
            
            results = []
            
            # Process each brand
            for brand in brands:
                try:
                    brand_result = await _collect_brand_mentions_async(str(brand.id), hours_back=1)
                    results.append(brand_result)
                    
                    # Small delay between brands to avoid rate limits
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error collecting mentions for brand {brand.name}: {str(e)}")
                    results.append({
                        "status": "error",
                        "brand_id": str(brand.id),
                        "brand_name": brand.name,
                        "error": str(e)
                    })
            
            total_mentions = sum(r.get("total_mentions", 0) for r in results)
            
            return {
                "status": "completed",
                "total_brands": len(brands),
                "total_mentions": total_mentions,
                "brand_results": results,
                "collected_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in _collect_all_mentions_async: {str(e)}")
            raise


@celery_app.task(bind=True)
def collect_platform_mentions(self, platform: str, brand_id: str = None, hours_back: int = 24):
    """Collect mentions from a specific platform"""
    try:
        return asyncio.run(_collect_platform_mentions_async(platform, brand_id, hours_back))
    except Exception as e:
        logger.error(f"Error in collect_platform_mentions: {str(e)}")
        self.retry(countdown=120, max_retries=3)


async def _collect_platform_mentions_async(platform: str, brand_id: str = None, hours_back: int = 24):
    """Async implementation of platform-specific mention collection"""
    async with AsyncSessionLocal() as db:
        try:
            # Get collector for platform
            collectors = {
                "twitter": TwitterCollector(),
                "reddit": RedditCollector(),
                "news": NewsCollector(),
                "youtube": YouTubeCollector()
            }
            
            collector = collectors.get(platform)
            if not collector:
                return {"status": "error", "message": f"Unknown platform: {platform}"}
            
            if not collector.is_configured():
                return {"status": "not_configured", "message": f"{platform} not configured"}
            
            # Get brands to process
            if brand_id:
                result = await db.execute(select(Brand).where(Brand.id == brand_id))
                brands = [result.scalar_one_or_none()]
                if not brands[0]:
                    return {"status": "error", "message": "Brand not found"}
            else:
                result = await db.execute(select(Brand).where(Brand.is_active == True))
                brands = result.scalars().all()
            
            total_mentions = 0
            brand_results = []
            
            for brand in brands:
                try:
                    mentions = await collector.safe_collect(brand, hours_back)
                    
                    # Save mentions
                    saved_count = 0
                    for mention_data in mentions:
                        # Check for duplicates
                        existing = await db.execute(
                            select(Mention).where(
                                Mention.platform == mention_data["platform"],
                                Mention.platform_id == mention_data["platform_id"]
                            )
                        )
                        
                        if existing.scalar_one_or_none():
                            continue
                        
                        mention = Mention(**mention_data)
                        db.add(mention)
                        saved_count += 1
                    
                    await db.commit()
                    
                    brand_results.append({
                        "brand_id": str(brand.id),
                        "brand_name": brand.name,
                        "mentions": saved_count
                    })
                    total_mentions += saved_count
                    
                except Exception as e:
                    logger.error(f"Error collecting {platform} mentions for brand {brand.name}: {str(e)}")
                    brand_results.append({
                        "brand_id": str(brand.id),
                        "brand_name": brand.name,
                        "error": str(e)
                    })
            
            return {
                "status": "completed",
                "platform": platform,
                "total_mentions": total_mentions,
                "brand_results": brand_results,
                "collected_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in _collect_platform_mentions_async: {str(e)}")
            raise


@celery_app.task
def cleanup_old_data():
    """Clean up old mentions and processed data"""
    try:
        return asyncio.run(_cleanup_old_data_async())
    except Exception as e:
        logger.error(f"Error in cleanup_old_data: {str(e)}")


async def _cleanup_old_data_async():
    """Async implementation of data cleanup"""
    async with AsyncSessionLocal() as db:
        try:
            # Delete mentions older than 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            old_mentions = await db.execute(
                select(Mention).where(Mention.collected_at < cutoff_date)
            )
            
            mentions_to_delete = old_mentions.scalars().all()
            deleted_count = 0
            
            for mention in mentions_to_delete:
                await db.delete(mention)
                deleted_count += 1
            
            await db.commit()
            
            logger.info(f"Cleaned up {deleted_count} old mentions")
            
            return {
                "status": "completed",
                "deleted_mentions": deleted_count,
                "cutoff_date": cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in _cleanup_old_data_async: {str(e)}")
            raise


# Utility function to trigger collection manually
def trigger_brand_collection(brand_id: str, hours_back: int = 24):
    """Trigger manual collection for a brand"""
    return collect_brand_mentions.delay(brand_id, hours_back)


def trigger_platform_collection(platform: str, brand_id: str = None, hours_back: int = 24):
    """Trigger manual collection for a platform"""
    return collect_platform_mentions.delay(platform, brand_id, hours_back)