import random
import aiohttp
import asyncio
import logging
from typing import List, Optional, Dict, Set
from urllib.parse import unquote
from redis_storage import RedisStorage

logger = logging.getLogger(__name__)


class UserQueue:
    """Individual user's video queue"""

    def __init__(self, all_videos: List[str], existing_queue: Optional[List[str]] = None, existing_index: int = 0):
        if existing_queue and len(existing_queue) == len(all_videos):
            # Restore from Redis
            self.queue = existing_queue
            self.current_index = existing_index
            logger.debug(f"Restored user queue from Redis: {len(self.queue)} videos, index {self.current_index}")
        else:
            # Create new shuffled queue
            self.queue: List[str] = all_videos.copy()
            random.shuffle(self.queue)
            self.current_index = 0
            logger.debug(f"Created new user queue with {len(self.queue)} videos")

    def to_dict(self) -> dict:
        """Serialize queue to dict for Redis storage"""
        return {
            "queue": self.queue,
            "current_index": self.current_index
        }


class VideoManager:
    """Manages video queues per user - ensures all videos play before repeating for each user"""

    def __init__(self, json_url: str):
        self.json_url = json_url
        self.all_videos: List[str] = []
        self.user_queues: Dict[int, UserQueue] = {}  # user_id -> UserQueue
        self.redis_storage = RedisStorage()  # Initialize Redis storage
        self._refresh_task: Optional[asyncio.Task] = None  # Background refresh task

    async def fetch_videos(self, merge_new: bool = False) -> bool:
        """Fetch videos from JSON URL

        Args:
            merge_new: If True, merge new videos into existing queues instead of clearing
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.json_url) as response:
                    if response.status == 200:
                        new_videos = await response.json()
                        logger.info(f"Fetched {len(new_videos)} videos from {self.json_url}")

                        if merge_new and self.all_videos:
                            # Merge new videos into existing queues
                            await self._merge_new_videos(new_videos)
                        else:
                            # Initial fetch or source switch - replace all
                            self.all_videos = new_videos
                            # Clear existing user queues when source changes
                            self.user_queues.clear()

                        return True
                    else:
                        logger.error(f"Failed to fetch videos: HTTP {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error fetching videos: {e}")
            return False

    async def _merge_new_videos(self, new_videos: List[str]):
        """Merge new videos into existing queues intelligently"""
        old_videos_set: Set[str] = set(self.all_videos)
        new_videos_set: Set[str] = set(new_videos)

        # Find added and removed videos
        added_videos = list(new_videos_set - old_videos_set)
        removed_videos = old_videos_set - new_videos_set

        if not added_videos and not removed_videos:
            logger.debug("No changes in video list")
            return

        if added_videos:
            logger.info(f"➕ Found {len(added_videos)} new videos")

            # Add new videos to all user queues after current position
            for user_id, user_queue in self.user_queues.items():
                # Get remaining videos (not yet played)
                remaining_videos = user_queue.queue[user_queue.current_index:]

                # Shuffle new videos
                shuffled_new = added_videos.copy()
                random.shuffle(shuffled_new)

                # Insert new videos into remaining queue
                # This ensures new videos are added to current round
                user_queue.queue = (
                    user_queue.queue[:user_queue.current_index] +  # Already played
                    remaining_videos + shuffled_new  # Remaining + new videos
                )

                # Save updated queue to Redis
                self._save_user_queue(user_id)
                logger.debug(f"Added {len(added_videos)} new videos to user {user_id}'s queue")

        if removed_videos:
            logger.info(f"➖ Removed {len(removed_videos)} videos from source")

            # Remove deleted videos from all user queues
            for user_id, user_queue in self.user_queues.items():
                original_length = len(user_queue.queue)

                # Filter out removed videos
                user_queue.queue = [v for v in user_queue.queue if v not in removed_videos]

                # Adjust current index if needed
                if user_queue.current_index > len(user_queue.queue):
                    user_queue.current_index = len(user_queue.queue)

                removed_count = original_length - len(user_queue.queue)
                if removed_count > 0:
                    self._save_user_queue(user_id)
                    logger.debug(f"Removed {removed_count} videos from user {user_id}'s queue")

        # Update master list
        self.all_videos = new_videos
        logger.info(f"✅ Video list updated: {len(self.all_videos)} total videos")

    def _get_user_queue(self, user_id: int) -> UserQueue:
        """Get or create a user's queue, with Redis persistence"""
        if user_id not in self.user_queues:
            # Try to load from Redis first
            saved_data = self.redis_storage.load_user_queue(user_id)
            if saved_data and isinstance(saved_data, dict):
                # Restore from Redis
                queue_data = saved_data.get("queue", [])
                index = saved_data.get("current_index", 0)
                logger.info(f"Restored queue for user {user_id} from Redis")
                self.user_queues[user_id] = UserQueue(self.all_videos, queue_data, index)
            else:
                # Create new queue
                logger.info(f"Creating new queue for user {user_id}")
                self.user_queues[user_id] = UserQueue(self.all_videos)
                # Save to Redis
                self._save_user_queue(user_id)
        return self.user_queues[user_id]

    def _save_user_queue(self, user_id: int):
        """Save user queue to Redis"""
        if user_id in self.user_queues:
            queue_data = self.user_queues[user_id].to_dict()
            self.redis_storage.save_user_queue(user_id, queue_data)

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

        # Save to Redis after each video selection
        self._save_user_queue(user_id)

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

    async def start_auto_refresh(self, interval_minutes: int = 10):
        """Start automatic video list refresh task

        Args:
            interval_minutes: Refresh interval in minutes (default: 10)
        """
        if self._refresh_task and not self._refresh_task.done():
            logger.warning("Auto-refresh task already running")
            return

        logger.info(f"🔄 Starting auto-refresh task (every {interval_minutes} minutes)")
        self._refresh_task = asyncio.create_task(self._auto_refresh_loop(interval_minutes))

    async def _auto_refresh_loop(self, interval_minutes: int):
        """Background task to refresh video list periodically"""
        interval_seconds = interval_minutes * 60

        while True:
            try:
                await asyncio.sleep(interval_seconds)
                logger.info("🔄 Auto-refreshing video list...")
                success = await self.fetch_videos(merge_new=True)

                if success:
                    logger.info("✅ Auto-refresh completed successfully")
                else:
                    logger.warning("⚠️  Auto-refresh failed, will retry next interval")

            except asyncio.CancelledError:
                logger.info("🛑 Auto-refresh task cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Error in auto-refresh task: {e}")
                # Continue the loop even if there's an error

    def stop_auto_refresh(self):
        """Stop the automatic refresh task"""
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
            logger.info("🛑 Stopped auto-refresh task")

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
