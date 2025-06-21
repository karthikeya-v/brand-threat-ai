from newsapi import NewsApiClient
from typing import List, Dict
from datetime import datetime, timedelta
import logging

from app.core.config import settings
from app.models.brand import Brand
from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class NewsCollector(BaseCollector):
    """Collect mentions from News API"""
    
    def __init__(self):
        super().__init__("news")
        self.api_key = settings.NEWS_API_KEY
        self.enabled = self.is_configured()
        
        if self.enabled:
            try:
                self.newsapi = NewsApiClient(api_key=self.api_key)
                # Test the API key
                self.newsapi.get_sources()
            except Exception as e:
                logger.error(f"Failed to initialize News API client: {str(e)}")
                self.enabled = False
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    async def collect_mentions(self, brand: Brand, hours_back: int = 24) -> List[Dict]:
        if not self.enabled:
            return []
        
        mentions = []
        
        try:
            # Calculate date range
            to_date = datetime.utcnow()
            from_date = to_date - timedelta(hours=hours_back)
            
            # Search for each keyword
            for keyword in brand.keywords:
                try:
                    # Search everything
                    articles = self.newsapi.get_everything(
                        q=keyword,
                        from_param=from_date.strftime('%Y-%m-%d'),
                        to=to_date.strftime('%Y-%m-%d'),
                        language='en',
                        sort_by='publishedAt',
                        page_size=100
                    )
                    
                    if articles['status'] == 'ok':
                        for article in articles['articles']:
                            # Skip if no content
                            if not article.get('description') and not article.get('content'):
                                continue
                            
                            # Combine title and description for content
                            content_parts = []
                            if article.get('title'):
                                content_parts.append(article['title'])
                            if article.get('description'):
                                content_parts.append(article['description'])
                            if article.get('content'):
                                # Clean up content (remove source attribution)
                                content = article['content']
                                if '[+' in content:
                                    content = content.split('[+')[0].strip()
                                content_parts.append(content)
                            
                            full_content = '\n\n'.join(content_parts)
                            
                            # Filter by keywords
                            if not self.filter_by_keywords(full_content, brand.keywords):
                                continue
                            
                            # Parse published date
                            published_at = datetime.utcnow()
                            if article.get('publishedAt'):
                                try:
                                    published_at = datetime.fromisoformat(
                                        article['publishedAt'].replace('Z', '+00:00')
                                    )
                                except:
                                    pass
                            
                            mention = self.create_mention_dict(
                                brand_id=str(brand.id),
                                platform_id=article.get('url', ''),
                                content=full_content,
                                author=article.get('author') or article.get('source', {}).get('name'),
                                author_followers=0,  # News articles don't have follower counts
                                engagement_count=0,  # News API doesn't provide engagement metrics
                                url=article.get('url'),
                                title=article.get('title'),
                                published_at=published_at
                            )
                            mentions.append(mention)
                            
                except Exception as e:
                    logger.debug(f"Error searching news for keyword '{keyword}': {str(e)}")
                    continue
            
            # Also search top headlines
            try:
                headlines = self.newsapi.get_top_headlines(
                    q=' OR '.join(brand.keywords),
                    language='en',
                    page_size=50
                )
                
                if headlines['status'] == 'ok':
                    for article in headlines['articles']:
                        if not article.get('description'):
                            continue
                        
                        content_parts = []
                        if article.get('title'):
                            content_parts.append(article['title'])
                        if article.get('description'):
                            content_parts.append(article['description'])
                        
                        full_content = '\n\n'.join(content_parts)
                        
                        if self.filter_by_keywords(full_content, brand.keywords):
                            published_at = datetime.utcnow()
                            if article.get('publishedAt'):
                                try:
                                    published_at = datetime.fromisoformat(
                                        article['publishedAt'].replace('Z', '+00:00')
                                    )
                                except:
                                    pass
                            
                            mention = self.create_mention_dict(
                                brand_id=str(brand.id),
                                platform_id=article.get('url', ''),
                                content=full_content,
                                author=article.get('author') or article.get('source', {}).get('name'),
                                author_followers=0,
                                engagement_count=0,
                                url=article.get('url'),
                                title=article.get('title'),
                                published_at=published_at
                            )
                            mentions.append(mention)
                            
            except Exception as e:
                logger.debug(f"Error getting top headlines: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error collecting news mentions: {str(e)}")
            return []
        
        # Remove duplicates based on URL
        unique_mentions = {}
        for mention in mentions:
            url = mention.get("url", mention.get("platform_id", ""))
            if url:
                unique_mentions[url] = mention
        
        return list(unique_mentions.values())
    
    async def get_sources(self, category: str = None, language: str = 'en') -> List[Dict]:
        """Get available news sources"""
        if not self.enabled:
            return []
        
        try:
            sources = self.newsapi.get_sources(
                category=category,
                language=language
            )
            
            if sources['status'] == 'ok':
                return sources['sources']
            
        except Exception as e:
            logger.error(f"Error getting news sources: {str(e)}")
        
        return []
    
    async def search_by_source(self, source_id: str, query: str) -> List[Dict]:
        """Search articles from a specific news source"""
        if not self.enabled:
            return []
        
        try:
            articles = self.newsapi.get_everything(
                q=query,
                sources=source_id,
                language='en',
                sort_by='publishedAt',
                page_size=50
            )
            
            if articles['status'] == 'ok':
                return articles['articles']
                
        except Exception as e:
            logger.error(f"Error searching by source: {str(e)}")
        
        return []