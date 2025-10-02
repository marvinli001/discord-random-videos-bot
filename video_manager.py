import random
import aiohttp
import logging
from typing import List, Optional
from urllib.parse import unquote

logger = logging.getLogger(__name__)


class VideoManager:
    """Manages video queue with shuffle logic - ensures all videos play before repeating"""

    def __init__(self, json_url: str):
        self.json_url = json_url
        self.all_videos: List[str] = []
        self.queue: List[str] = []
        self.current_index = 0

    async def fetch_videos(self) -> bool:
        """Fetch videos from JSON URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.json_url) as response:
                    if response.status == 200:
                        self.all_videos = await response.json()
                        logger.info(f"Fetched {len(self.all_videos)} videos from {self.json_url}")
                        self._shuffle_queue()
                        return True
                    else:
                        logger.error(f"Failed to fetch videos: HTTP {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error fetching videos: {e}")
            return False

    def _shuffle_queue(self):
        """Create a new shuffled queue from all videos"""
        self.queue = self.all_videos.copy()
        random.shuffle(self.queue)
        self.current_index = 0
        logger.info(f"Shuffled queue with {len(self.queue)} videos")

    def get_next_video(self) -> Optional[str]:
        """Get next video from queue, reshuffle when queue is exhausted"""
        if not self.queue:
            logger.warning("No videos available in queue")
            return None

        # If we've played all videos, start a new round
        if self.current_index >= len(self.queue):
            logger.info("Queue exhausted, starting new shuffle round")
            self._shuffle_queue()

        video_url = self.queue[self.current_index]
        self.current_index += 1

        logger.debug(f"Next video ({self.current_index}/{len(self.queue)}): {video_url}")
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

    def get_queue_status(self) -> dict:
        """Get current queue status"""
        return {
            "total_videos": len(self.all_videos),
            "queue_size": len(self.queue),
            "current_position": self.current_index,
            "videos_remaining": len(self.queue) - self.current_index
        }
