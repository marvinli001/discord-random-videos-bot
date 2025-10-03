"""
TikTok Video Manager - Real-time search and queue management
"""
import random
import asyncio
import logging
from typing import List, Optional, Dict
from redis_storage import RedisStorage

logger = logging.getLogger(__name__)


class TikTokQueue:
    """Individual user's TikTok video queue"""

    def __init__(self, all_videos: List[str], existing_queue: Optional[List[str]] = None, existing_index: int = 0):
        if existing_queue and len(existing_queue) == len(all_videos):
            # Restore from Redis
            self.queue = existing_queue
            self.current_index = existing_index
            logger.debug(f"Restored TikTok queue from Redis: {len(self.queue)} videos, index {self.current_index}")
        else:
            # Create new shuffled queue
            self.queue: List[str] = all_videos.copy()
            random.shuffle(self.queue)
            self.current_index = 0
            logger.debug(f"Created new TikTok queue with {len(self.queue)} videos")

    def to_dict(self) -> dict:
        """Serialize queue to dict for Redis storage"""
        return {
            "queue": self.queue,
            "current_index": self.current_index
        }


class TikTokManager:
    """Manages TikTok video search and queues per user"""

    def __init__(self, hashtag: str = "cosplaydance"):
        self.hashtag = hashtag
        self.all_videos: List[str] = []
        self.user_queues: Dict[int, TikTokQueue] = {}
        self.redis_storage = RedisStorage()
        self._api = None
        self._last_fetch_time = 0
        self._fetch_interval = 3600  # Refresh every hour

    async def _init_api(self):
        """Initialize TikTok API (lazy loading)"""
        if self._api is None:
            try:
                # Try lightweight approach without Playwright
                import aiohttp
                import os

                self._api = "lightweight"  # Mark as initialized with lightweight mode
                self._ms_token = os.getenv('TIKTOK_MS_TOKEN')
                logger.info("✅ Using lightweight TikTok API (no browser required)")
            except Exception as e:
                logger.error(f"❌ Failed to initialize TikTok API: {e}")
                self._api = None

    async def fetch_videos(self, count: int = 50) -> bool:
        """Search TikTok for videos by hashtag using lightweight API"""
        import time
        import aiohttp

        current_time = time.time()

        # Check if we need to refresh
        if self.all_videos and (current_time - self._last_fetch_time) < self._fetch_interval:
            logger.info(f"Using cached TikTok videos ({len(self.all_videos)} videos)")
            return True

        try:
            await self._init_api()

            if not self._api:
                logger.warning("⚠️  TikTok API not available, using fallback")
                return await self._fetch_fallback()

            logger.info(f"🔍 Searching TikTok hashtag: #{self.hashtag} (lightweight mode)")

            # Use TikTok's web API directly (no browser needed)
            videos = await self._fetch_via_web_api(count)

            if videos:
                self.all_videos = videos
                self._last_fetch_time = current_time
                logger.info(f"✅ Fetched {len(videos)} TikTok videos for #{self.hashtag}")
                return True
            else:
                logger.warning(f"⚠️  No videos found for #{self.hashtag}, using fallback")
                return await self._fetch_fallback()

        except Exception as e:
            logger.error(f"❌ Error fetching TikTok videos: {e}")
            return await self._fetch_fallback()

    async def _fetch_via_web_api(self, count: int = 50) -> List[str]:
        """Fetch TikTok videos using web API (no browser required)"""
        import aiohttp
        import json

        videos = []

        try:
            # TikTok web API endpoint for hashtag challenge
            url = f"https://www.tiktok.com/api/challenge/item_list/"

            params = {
                "challengeName": self.hashtag,
                "count": count,
                "cursor": 0
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": f"https://www.tiktok.com/tag/{self.hashtag}"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()

                        if "itemList" in data:
                            for item in data["itemList"][:count]:
                                try:
                                    video_id = item.get("id")
                                    author = item.get("author", {}).get("uniqueId")
                                    if video_id and author:
                                        video_url = f"https://tiktok.com/@{author}/video/{video_id}"
                                        videos.append(video_url)
                                        logger.debug(f"Found video: {video_url}")
                                except Exception as e:
                                    continue
                    else:
                        logger.warning(f"Web API returned status {response.status}")

        except Exception as e:
            logger.warning(f"Web API fetch failed: {e}")

        return videos

    async def _fetch_fallback(self) -> bool:
        """Fallback: use a default set of videos if API fails"""
        logger.info("Using fallback TikTok video list")
        self.all_videos = [
            "https://tiktok.com/@cosplay.world/video/7123456789012345678",
            "https://tiktok.com/@anime.cosplay/video/7234567890123456789",
            "https://tiktok.com/@kpop.dance/video/7345678901234567890",
        ]
        return True

    def _get_user_queue(self, user_id: int) -> TikTokQueue:
        """Get or create a user's TikTok queue, with Redis persistence"""
        if user_id not in self.user_queues:
            # Try to load from Redis first
            saved_data = self.redis_storage.load_user_queue(user_id, f"tiktok_{self.hashtag}")
            if saved_data and isinstance(saved_data, dict):
                # Restore from Redis
                queue_data = saved_data.get("queue", [])
                index = saved_data.get("current_index", 0)
                logger.info(f"Restored TikTok queue for user {user_id} from Redis")
                self.user_queues[user_id] = TikTokQueue(self.all_videos, queue_data, index)
            else:
                # Create new queue
                logger.info(f"Creating new TikTok queue for user {user_id}")
                self.user_queues[user_id] = TikTokQueue(self.all_videos)
                # Save to Redis
                self._save_user_queue(user_id)

        return self.user_queues[user_id]

    def _save_user_queue(self, user_id: int):
        """Save user TikTok queue to Redis"""
        if user_id in self.user_queues:
            queue_data = self.user_queues[user_id].to_dict()
            self.redis_storage.save_user_queue(user_id, queue_data, f"tiktok_{self.hashtag}")

    def get_next_video(self, user_id: int) -> Optional[str]:
        """Get next TikTok video from user's queue, reshuffle when exhausted"""
        if not self.all_videos:
            logger.warning("No TikTok videos available")
            return None

        user_queue = self._get_user_queue(user_id)

        # If user has played all videos, start a new round
        if user_queue.current_index >= len(user_queue.queue):
            logger.info(f"User {user_id} TikTok queue exhausted, starting new shuffle round")
            user_queue.queue = self.all_videos.copy()
            random.shuffle(user_queue.queue)
            user_queue.current_index = 0

        video_url = user_queue.queue[user_queue.current_index]
        user_queue.current_index += 1

        # Convert to vxTikTok for Discord embedding
        video_url = self._convert_to_embeddable(video_url)

        # Save to Redis after each video selection
        self._save_user_queue(user_id)

        logger.debug(f"User {user_id} - Next TikTok ({user_queue.current_index}/{len(user_queue.queue)}): {video_url}")
        return video_url

    @staticmethod
    def _convert_to_embeddable(url: str) -> str:
        """Convert TikTok URL to embeddable format for Discord"""
        # Replace tiktok.com with vxtiktok.com for Discord embedding
        if 'tiktok.com' in url and 'vxtiktok.com' not in url:
            url = url.replace('tiktok.com', 'vxtiktok.com')
        return url

    @staticmethod
    def extract_video_id(url: str) -> str:
        """Extract video ID or title from TikTok URL"""
        try:
            # Extract video ID from URL
            # Example: https://vxtiktok.com/@user/video/123 -> 123
            parts = url.rstrip('/').split('/')
            if 'video' in parts:
                idx = parts.index('video')
                if idx + 1 < len(parts):
                    video_id = parts[idx + 1]
                    return f"TikTok {video_id}"
            return "TikTok Video"
        except Exception as e:
            logger.error(f"Error extracting TikTok video ID from {url}: {e}")
            return "TikTok Video"

    async def close(self):
        """Close TikTok API session"""
        if self._api:
            try:
                await self._api.close()
                logger.info("TikTok API session closed")
            except Exception as e:
                logger.error(f"Error closing TikTok API: {e}")

    def get_queue_status(self, user_id: int) -> dict:
        """Get user's TikTok queue status"""
        if user_id not in self.user_queues:
            return {
                "total_videos": len(self.all_videos),
                "queue_size": 0,
                "current_position": 0,
                "videos_remaining": len(self.all_videos)
            }

        user_queue = self.user_queues[user_id]
        return {
            "total_videos": len(self.all_videos),
            "queue_size": len(user_queue.queue),
            "current_position": user_queue.current_index,
            "videos_remaining": len(user_queue.queue) - user_queue.current_index
        }
