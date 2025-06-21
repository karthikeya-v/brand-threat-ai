import praw
from typing import List, Dict
from datetime import datetime, timedelta
import logging

from app.core.config import settings
from app.models.brand import Brand
from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class RedditCollector(BaseCollector):
    """Collect mentions from Reddit API"""
    
    def __init__(self):
        super().__init__("reddit")
        self.client_id = settings.REDDIT_CLIENT_ID
        self.client_secret = settings.REDDIT_CLIENT_SECRET
        self.enabled = self.is_configured()
        
        if self.enabled:
            try:
                self.reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent="ThreatWatch:v1.0 (by /u/threatwatch)"
                )
                # Test connection
                self.reddit.auth.scopes()
            except Exception as e:
                logger.error(f"Failed to initialize Reddit client: {str(e)}")
                self.enabled = False
    
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)
    
    async def collect_mentions(self, brand: Brand, hours_back: int = 24) -> List[Dict]:
        if not self.enabled:
            return []
        
        mentions = []
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        try:
            # Search across multiple subreddits
            subreddits_to_search = [
                "all",  # Global search
                "business",
                "technology", 
                "news",
                "reviews",
                "stocks",
                "investing",
                "startups"
            ]
            
            for keyword in brand.keywords:
                for subreddit_name in subreddits_to_search:
                    try:
                        if subreddit_name == "all":
                            subreddit = self.reddit.subreddit("all")
                        else:
                            subreddit = self.reddit.subreddit(subreddit_name)
                        
                        # Search posts
                        for submission in subreddit.search(
                            query=keyword,
                            sort="new",
                            time_filter="day",
                            limit=50
                        ):
                            created_time = datetime.fromtimestamp(submission.created_utc)
                            
                            if created_time < cutoff_time:
                                continue
                            
                            # Check if relevant
                            if not self.filter_by_keywords(submission.title + " " + submission.selftext, brand.keywords):
                                continue
                            
                            mention = self.create_mention_dict(
                                brand_id=str(brand.id),
                                platform_id=submission.id,
                                content=f"{submission.title}\n\n{submission.selftext}",
                                author=submission.author.name if submission.author else "[deleted]",
                                author_followers=0,  # Reddit doesn't have follower count
                                engagement_count=submission.score + submission.num_comments,
                                url=f"https://reddit.com{submission.permalink}",
                                title=submission.title,
                                published_at=created_time
                            )
                            mentions.append(mention)
                        
                        # Search comments in hot posts
                        for submission in subreddit.hot(limit=20):
                            try:
                                submission.comments.replace_more(limit=0)
                                for comment in submission.comments.list():
                                    if hasattr(comment, 'body') and comment.body:
                                        created_time = datetime.fromtimestamp(comment.created_utc)
                                        
                                        if created_time < cutoff_time:
                                            continue
                                        
                                        if self.filter_by_keywords(comment.body, brand.keywords):
                                            mention = self.create_mention_dict(
                                                brand_id=str(brand.id),
                                                platform_id=comment.id,
                                                content=comment.body,
                                                author=comment.author.name if comment.author else "[deleted]",
                                                author_followers=0,
                                                engagement_count=comment.score,
                                                url=f"https://reddit.com{comment.permalink}",
                                                title=f"Comment on: {submission.title}",
                                                published_at=created_time
                                            )
                                            mentions.append(mention)
                            except Exception as e:
                                logger.debug(f"Error processing Reddit comments: {str(e)}")
                                continue
                    
                    except Exception as e:
                        logger.debug(f"Error searching Reddit subreddit {subreddit_name}: {str(e)}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error collecting Reddit mentions: {str(e)}")
            return []
        
        # Remove duplicates based on platform_id
        unique_mentions = {}
        for mention in mentions:
            unique_mentions[mention["platform_id"]] = mention
        
        return list(unique_mentions.values())
    
    async def get_subreddit_posts(self, subreddit_name: str, limit: int = 25) -> List[Dict]:
        """Get recent posts from a specific subreddit"""
        if not self.enabled:
            return []
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            posts = []
            
            for submission in subreddit.new(limit=limit):
                posts.append({
                    "id": submission.id,
                    "title": submission.title,
                    "content": submission.selftext,
                    "author": submission.author.name if submission.author else "[deleted]",
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                    "created_utc": submission.created_utc,
                    "url": f"https://reddit.com{submission.permalink}"
                })
            
            return posts
            
        except Exception as e:
            logger.error(f"Error getting subreddit posts: {str(e)}")
            return []
    
    async def search_subreddit(self, subreddit_name: str, query: str, limit: int = 50) -> List[Dict]:
        """Search for posts in a specific subreddit"""
        if not self.enabled:
            return []
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            posts = []
            
            for submission in subreddit.search(query, sort="new", limit=limit):
                posts.append({
                    "id": submission.id,
                    "title": submission.title,
                    "content": submission.selftext,
                    "author": submission.author.name if submission.author else "[deleted]",
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                    "created_utc": submission.created_utc,
                    "url": f"https://reddit.com{submission.permalink}",
                    "subreddit": subreddit_name
                })
            
            return posts
            
        except Exception as e:
            logger.error(f"Error searching subreddit: {str(e)}")
            return []