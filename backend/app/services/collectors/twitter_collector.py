import httpx
from typing import List, Dict
from datetime import datetime, timedelta
import logging

from app.core.config import settings
from app.models.brand import Brand
from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class TwitterCollector(BaseCollector):
    """Collect mentions from Twitter API v2"""
    
    def __init__(self):
        super().__init__("twitter")
        self.bearer_token = settings.TWITTER_BEARER_TOKEN
        self.enabled = self.is_configured()
        
        self.base_url = "https://api.twitter.com/2"
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        } if self.bearer_token else {}
    
    def is_configured(self) -> bool:
        return bool(self.bearer_token)
    
    async def collect_mentions(self, brand: Brand, hours_back: int = 24) -> List[Dict]:
        if not self.enabled:
            return []
        
        mentions = []
        
        # Build search query
        query_parts = []
        
        # Add brand keywords
        for keyword in brand.keywords:
            if ' ' in keyword:
                query_parts.append(f'"{keyword}"')
            else:
                query_parts.append(keyword)
        
        # Combine with OR
        search_query = " OR ".join(query_parts)
        
        # Add language and result type filters
        search_query += " -is:retweet lang:en"
        
        # Calculate start time
        start_time = datetime.utcnow() - timedelta(hours=hours_back)
        start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        params = {
            "query": search_query,
            "tweet.fields": "id,text,author_id,created_at,public_metrics,context_annotations",
            "user.fields": "id,username,name,public_metrics",
            "expansions": "author_id",
            "max_results": 100,
            "start_time": start_time_str
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/tweets/search/recent",
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Twitter API error: {response.status_code} - {response.text}")
                    return []
                
                data = response.json()
                
                if "data" not in data:
                    logger.info("No tweets found")
                    return []
                
                # Process tweets
                tweets = data["data"]
                users = {user["id"]: user for user in data.get("includes", {}).get("users", [])}
                
                for tweet in tweets:
                    # Get author info
                    author_id = tweet.get("author_id")
                    author_info = users.get(author_id, {})
                    
                    # Extract metrics
                    metrics = tweet.get("public_metrics", {})
                    engagement = (
                        metrics.get("retweet_count", 0) +
                        metrics.get("like_count", 0) +
                        metrics.get("reply_count", 0) +
                        metrics.get("quote_count", 0)
                    )
                    
                    # Create mention
                    mention = self.create_mention_dict(
                        brand_id=str(brand.id),
                        platform_id=tweet["id"],
                        content=tweet["text"],
                        author=author_info.get("username"),
                        author_followers=author_info.get("public_metrics", {}).get("followers_count", 0),
                        engagement_count=engagement,
                        url=f"https://twitter.com/{author_info.get('username')}/status/{tweet['id']}" if author_info.get('username') else None,
                        published_at=datetime.fromisoformat(tweet["created_at"].replace('Z', '+00:00'))
                    )
                    
                    # Filter by keywords (double-check)
                    if self.filter_by_keywords(tweet["text"], brand.keywords):
                        mentions.append(mention)
                
        except Exception as e:
            logger.error(f"Error collecting Twitter mentions: {str(e)}")
            return []
        
        return mentions
    
    async def get_user_tweets(self, username: str, count: int = 10) -> List[Dict]:
        """Get recent tweets from a specific user"""
        if not self.enabled:
            return []
        
        try:
            # First get user ID
            async with httpx.AsyncClient() as client:
                user_response = await client.get(
                    f"{self.base_url}/users/by/username/{username}",
                    headers=self.headers,
                    timeout=30.0
                )
                
                if user_response.status_code != 200:
                    return []
                
                user_data = user_response.json()
                user_id = user_data["data"]["id"]
                
                # Get user tweets
                tweet_response = await client.get(
                    f"{self.base_url}/users/{user_id}/tweets",
                    headers=self.headers,
                    params={
                        "tweet.fields": "id,text,created_at,public_metrics",
                        "max_results": min(count, 100)
                    },
                    timeout=30.0
                )
                
                if tweet_response.status_code != 200:
                    return []
                
                tweet_data = tweet_response.json()
                return tweet_data.get("data", [])
                
        except Exception as e:
            logger.error(f"Error getting user tweets: {str(e)}")
            return []
    
    async def search_hashtag(self, hashtag: str, count: int = 50) -> List[Dict]:
        """Search for tweets with specific hashtag"""
        if not self.enabled:
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/tweets/search/recent",
                    headers=self.headers,
                    params={
                        "query": f"#{hashtag} -is:retweet",
                        "tweet.fields": "id,text,author_id,created_at,public_metrics",
                        "user.fields": "id,username,public_metrics",
                        "expansions": "author_id",
                        "max_results": min(count, 100)
                    },
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    return []
                
                data = response.json()
                return data.get("data", [])
                
        except Exception as e:
            logger.error(f"Error searching hashtag: {str(e)}")
            return []