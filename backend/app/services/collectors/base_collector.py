from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import logging

from app.models.brand import Brand
from app.models.mention import Mention

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Base class for all platform collectors"""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.enabled = False
        
    @abstractmethod
    async def collect_mentions(self, brand: Brand, hours_back: int = 24) -> List[Dict]:
        """Collect mentions for a brand from the platform"""
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the collector is properly configured with API keys"""
        pass
    
    def create_mention_dict(
        self,
        brand_id: str,
        platform_id: Optional[str],
        content: str,
        author: Optional[str] = None,
        author_followers: Optional[int] = None,
        engagement_count: Optional[int] = None,
        url: Optional[str] = None,
        title: Optional[str] = None,
        published_at: Optional[datetime] = None
    ) -> Dict:
        """Create standardized mention dictionary"""
        
        return {
            "brand_id": brand_id,
            "platform": self.platform_name,
            "platform_id": platform_id,
            "url": url,
            "title": title,
            "content": content,
            "author": author,
            "author_followers": author_followers or 0,
            "engagement_count": engagement_count or 0,
            "published_at": published_at or datetime.utcnow(),
            "collected_at": datetime.utcnow(),
            "processed": False
        }
    
    def filter_by_keywords(self, content: str, keywords: List[str]) -> bool:
        """Check if content contains any of the brand keywords"""
        content_lower = content.lower()
        return any(keyword.lower() in content_lower for keyword in keywords)
    
    async def safe_collect(self, brand: Brand, hours_back: int = 24) -> List[Dict]:
        """Safely collect mentions with error handling"""
        try:
            if not self.is_configured():
                logger.warning(f"{self.platform_name} collector not configured")
                return []
            
            mentions = await self.collect_mentions(brand, hours_back)
            logger.info(f"Collected {len(mentions)} mentions from {self.platform_name} for brand {brand.name}")
            return mentions
            
        except Exception as e:
            logger.error(f"Error collecting from {self.platform_name}: {str(e)}")
            return []