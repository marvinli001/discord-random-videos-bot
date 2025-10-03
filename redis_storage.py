"""
Redis Storage Manager for persisting user shuffle queues
"""
import json
import logging
from typing import Optional, List, Dict
import redis
import os

logger = logging.getLogger(__name__)


class RedisStorage:
    """Manages Redis connections and data persistence"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.available = False
        self._connect()

    def _connect(self):
        """Connect to Redis using Railway-provided environment variables"""
        try:
            # Railway provides REDIS_URL or individual Redis variables
            redis_url = os.getenv('REDIS_URL')

            if redis_url:
                # Use REDIS_URL if available
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
            else:
                # Fallback to individual variables (REDIS_HOST, REDIS_PORT, etc.)
                redis_host = os.getenv('REDISHOST', 'localhost')
                redis_port = int(os.getenv('REDISPORT', 6379))
                redis_password = os.getenv('REDISPASSWORD')
                redis_user = os.getenv('REDISUSER', 'default')

                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    username=redis_user,
                    password=redis_password,
                    decode_responses=True,
                    socket_connect_timeout=5
                )

            # Test connection
            self.redis_client.ping()
            self.available = True
            logger.info("✅ Redis connected successfully")

        except Exception as e:
            logger.warning(f"⚠️  Redis not available: {e}. Running without persistence.")
            self.redis_client = None
            self.available = False

    def save_user_queue(self, user_id: int, queue: List[str]) -> bool:
        """Save user's shuffle queue to Redis"""
        if not self.available or not self.redis_client:
            return False

        try:
            key = f"user_queue:{user_id}"
            # Store as JSON string
            self.redis_client.set(key, json.dumps(queue))
            # Set expiration to 30 days
            self.redis_client.expire(key, 30 * 24 * 60 * 60)
            return True
        except Exception as e:
            logger.error(f"Failed to save queue for user {user_id}: {e}")
            return False

    def load_user_queue(self, user_id: int) -> Optional[List[str]]:
        """Load user's shuffle queue from Redis"""
        if not self.available or not self.redis_client:
            return None

        try:
            key = f"user_queue:{user_id}"
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to load queue for user {user_id}: {e}")
            return None

    def delete_user_queue(self, user_id: int) -> bool:
        """Delete user's shuffle queue from Redis"""
        if not self.available or not self.redis_client:
            return False

        try:
            key = f"user_queue:{user_id}"
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete queue for user {user_id}: {e}")
            return False

    def get_all_user_queues(self) -> Dict[int, List[str]]:
        """Get all user queues (for debugging/admin)"""
        if not self.available or not self.redis_client:
            return {}

        try:
            queues = {}
            for key in self.redis_client.scan_iter("user_queue:*"):
                user_id = int(key.split(":")[1])
                data = self.redis_client.get(key)
                if data:
                    queues[user_id] = json.loads(data)
            return queues
        except Exception as e:
            logger.error(f"Failed to get all queues: {e}")
            return {}

    def close(self):
        """Close Redis connection"""
        if self.redis_client:
            try:
                self.redis_client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
