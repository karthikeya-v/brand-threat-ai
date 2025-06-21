from googleapiclient.discovery import build
from typing import List, Dict
from datetime import datetime, timedelta
import logging

from app.core.config import settings
from app.models.brand import Brand
from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class YouTubeCollector(BaseCollector):
    """Collect mentions from YouTube API"""
    
    def __init__(self):
        super().__init__("youtube")
        self.api_key = settings.YOUTUBE_API_KEY
        self.enabled = self.is_configured()
        
        if self.enabled:
            try:
                self.youtube = build('youtube', 'v3', developerKey=self.api_key)
                # Test the API key
                self.youtube.search().list(part='snippet', q='test', maxResults=1).execute()
            except Exception as e:
                logger.error(f"Failed to initialize YouTube API client: {str(e)}")
                self.enabled = False
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    async def collect_mentions(self, brand: Brand, hours_back: int = 24) -> List[Dict]:
        if not self.enabled:
            return []
        
        mentions = []
        
        try:
            # Calculate date range
            published_after = (datetime.utcnow() - timedelta(hours=hours_back)).isoformat() + 'Z'
            
            # Search for each keyword
            for keyword in brand.keywords:
                try:
                    # Search videos
                    search_response = self.youtube.search().list(
                        q=keyword,
                        part='snippet',
                        type='video',
                        publishedAfter=published_after,
                        maxResults=50,
                        order='relevance'
                    ).execute()
                    
                    for search_result in search_response.get('items', []):
                        video_id = search_result['id']['videoId']
                        snippet = search_result['snippet']
                        
                        # Get video statistics
                        video_response = self.youtube.videos().list(
                            part='statistics',
                            id=video_id
                        ).execute()
                        
                        stats = video_response.get('items', [{}])[0].get('statistics', {})
                        
                        # Get channel info for subscriber count
                        channel_response = self.youtube.channels().list(
                            part='statistics',
                            id=snippet['channelId']
                        ).execute()
                        
                        channel_stats = channel_response.get('items', [{}])[0].get('statistics', {})
                        
                        # Combine title and description
                        content = f"{snippet['title']}\n\n{snippet.get('description', '')}"
                        
                        # Filter by keywords
                        if not self.filter_by_keywords(content, brand.keywords):
                            continue
                        
                        # Calculate engagement
                        engagement = (
                            int(stats.get('viewCount', 0)) +
                            int(stats.get('likeCount', 0)) +
                            int(stats.get('commentCount', 0))
                        )
                        
                        # Parse published date
                        published_at = datetime.fromisoformat(
                            snippet['publishedAt'].replace('Z', '+00:00')
                        )
                        
                        mention = self.create_mention_dict(
                            brand_id=str(brand.id),
                            platform_id=video_id,
                            content=content,
                            author=snippet['channelTitle'],
                            author_followers=int(channel_stats.get('subscriberCount', 0)),
                            engagement_count=engagement,
                            url=f"https://www.youtube.com/watch?v={video_id}",
                            title=snippet['title'],
                            published_at=published_at
                        )
                        mentions.append(mention)
                    
                    # Also search comments on popular videos
                    await self._search_comments(brand, keyword, mentions)
                    
                except Exception as e:
                    logger.debug(f"Error searching YouTube for keyword '{keyword}': {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error collecting YouTube mentions: {str(e)}")
            return []
        
        return mentions
    
    async def _search_comments(self, brand: Brand, keyword: str, mentions: List[Dict]):
        """Search comments on videos for brand mentions"""
        try:
            # Search for videos related to the keyword
            search_response = self.youtube.search().list(
                q=keyword,
                part='snippet',
                type='video',
                maxResults=10,
                order='relevance'
            ).execute()
            
            for search_result in search_response.get('items', []):
                video_id = search_result['id']['videoId']
                
                try:
                    # Get comments for this video
                    comments_response = self.youtube.commentThreads().list(
                        part='snippet',
                        videoId=video_id,
                        maxResults=50,
                        order='relevance'
                    ).execute()
                    
                    for comment_item in comments_response.get('items', []):
                        comment = comment_item['snippet']['topLevelComment']['snippet']
                        
                        # Filter by keywords
                        if not self.filter_by_keywords(comment['textOriginal'], brand.keywords):
                            continue
                        
                        # Parse published date
                        published_at = datetime.fromisoformat(
                            comment['publishedAt'].replace('Z', '+00:00')
                        )
                        
                        # Only include recent comments
                        cutoff_time = datetime.utcnow() - timedelta(hours=24)
                        if published_at < cutoff_time:
                            continue
                        
                        mention = self.create_mention_dict(
                            brand_id=str(brand.id),
                            platform_id=comment_item['id'],
                            content=comment['textOriginal'],
                            author=comment['authorDisplayName'],
                            author_followers=0,  # YouTube doesn't provide commenter follower count
                            engagement_count=int(comment.get('likeCount', 0)),
                            url=f"https://www.youtube.com/watch?v={video_id}&lc={comment_item['id']}",
                            title=f"Comment on: {search_result['snippet']['title']}",
                            published_at=published_at
                        )
                        mentions.append(mention)
                        
                except Exception as e:
                    logger.debug(f"Error getting comments for video {video_id}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.debug(f"Error searching YouTube comments: {str(e)}")
    
    async def get_channel_videos(self, channel_id: str, max_results: int = 25) -> List[Dict]:
        """Get recent videos from a specific channel"""
        if not self.enabled:
            return []
        
        try:
            search_response = self.youtube.search().list(
                channelId=channel_id,
                part='snippet',
                type='video',
                maxResults=max_results,
                order='date'
            ).execute()
            
            videos = []
            for item in search_response.get('items', []):
                videos.append({
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'published_at': item['snippet']['publishedAt'],
                    'channel_title': item['snippet']['channelTitle'],
                    'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                })
            
            return videos
            
        except Exception as e:
            logger.error(f"Error getting channel videos: {str(e)}")
            return []
    
    async def search_videos(self, query: str, max_results: int = 50) -> List[Dict]:
        """Search for videos with specific query"""
        if not self.enabled:
            return []
        
        try:
            search_response = self.youtube.search().list(
                q=query,
                part='snippet',
                type='video',
                maxResults=max_results,
                order='relevance'
            ).execute()
            
            videos = []
            for item in search_response.get('items', []):
                videos.append({
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'published_at': item['snippet']['publishedAt'],
                    'channel_title': item['snippet']['channelTitle'],
                    'channel_id': item['snippet']['channelId'],
                    'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                })
            
            return videos
            
        except Exception as e:
            logger.error(f"Error searching videos: {str(e)}")
            return []