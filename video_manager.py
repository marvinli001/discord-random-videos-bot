import random
import aiohttp
import logging
from typing import List, Optional, Dict
from urllib.parse import unquote

logger = logging.getLogger(__name__)


class UserQueue:
    """Individual user's video queue"""

    def __init__(self, all_videos: List[str]):
        self.queue: List[str] = all_videos.copy()
        random.shuffle(self.queue)
        self.current_index = 0
        logger.debug(f"Created new user queue with {len(self.queue)} videos")


class VideoManager:
    """Manages video queues per user - ensures all videos play before repeating for each user"""

    def __init__(self, json_url: str):
        self.json_url = json_url
        self.all_videos: List[str] = []
        self.user_queues: Dict[int, UserQueue] = {}  # user_id -> UserQueue

    async def fetch_videos(self) -> bool:
        """Fetch videos from JSON URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.json_url) as response:
                    if response.status == 200:
                        self.all_videos = await response.json()
                        logger.info(f"Fetched {len(self.all_videos)} videos from {self.json_url}")
                        # Clear existing user queues when source changes
                        self.user_queues.clear()
                        return True
                    else:
                        logger.error(f"Failed to fetch videos: HTTP {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error fetching videos: {e}")
            return False

    def _get_user_queue(self, user_id: int) -> UserQueue:
        """Get or create a user's queue"""
        if user_id not in self.user_queues:
            logger.info(f"Creating new queue for user {user_id}")
            self.user_queues[user_id] = UserQueue(self.all_videos)
        return self.user_queues[user_id]

    def get_next_video(self, user_id: int) -> Optional[str]:
        """Get next video from user's queue, reshuffle when queue is exhausted"""
        if not self.all_videos:
            logger.warning("No videos available")
            return None

        user_queue = self._get_user_queue(user_id)

        # If user has played all videos, start a new round
        if user_queue.current_index >= len(user_queue.queue):
            logger.info(f"User {user_id} queue exhausted, starting new shuffle round")
            user_queue.queue = self.all_videos.copy()
            random.shuffle(user_queue.queue)
            user_queue.current_index = 0

        video_url = user_queue.queue[user_queue.current_index]
        user_queue.current_index += 1

        logger.debug(f"User {user_id} - Next video ({user_queue.current_index}/{len(user_queue.queue)}): {video_url}")
        return video_url

    @staticmethod
    def extract_filename(url: str) -> str:
        """Extract and decode filename from URL"""
        try:
            # Get the last part of URL (filename)
            filename = url.split('/')[-1]
            # Decode URL encoding
            decoded = unquote(filename)
            return decoded
        except Exception as e:
            logger.error(f"Error extracting filename from {url}: {e}")
            return "视频.mp4"

    async def switch_source(self, new_json_url: str) -> bool:
        """Switch to a different video source"""
        logger.info(f"Switching video source to: {new_json_url}")
        self.json_url = new_json_url
        return await self.fetch_videos()

    def get_queue_status(self, user_id: int) -> dict:
        """Get user's queue status"""
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
