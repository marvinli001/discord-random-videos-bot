import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager that loads from .env and environment variables"""

    def __init__(self):
        load_dotenv()
        self.reload()

        # Store current values for change detection
        self._cached_values = {}

    def reload(self):
        """Reload configuration from environment"""
        load_dotenv(override=True)

        self.DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
        self.VIDEO_JSON_URL = os.getenv('VIDEO_JSON_URL', 'https://videos.vistru.cn/videos.json')
        self.DISCORD_ACTIVITY_NAME = os.getenv('DISCORD_ACTIVITY_NAME', '随机视频')

        # Validate required settings
        if not self.DISCORD_BOT_TOKEN:
            raise ValueError("DISCORD_BOT_TOKEN is required in .env or environment variables")

        logger.info(f"Configuration loaded - Activity: {self.DISCORD_ACTIVITY_NAME}, Video URL: {self.VIDEO_JSON_URL}")

    def has_changed(self) -> bool:
        """Check if environment variables have changed (for cloud deployment)"""
        current_values = {
            'DISCORD_BOT_TOKEN': os.getenv('DISCORD_BOT_TOKEN'),
            'VIDEO_JSON_URL': os.getenv('VIDEO_JSON_URL', 'https://videos.vistru.cn/videos.json'),
            'DISCORD_ACTIVITY_NAME': os.getenv('DISCORD_ACTIVITY_NAME', '随机视频')
        }

        # First run - cache current values
        if not self._cached_values:
            self._cached_values = current_values.copy()
            return False

        # Check for changes (ignore token for security)
        changed = (
            current_values['VIDEO_JSON_URL'] != self._cached_values.get('VIDEO_JSON_URL') or
            current_values['DISCORD_ACTIVITY_NAME'] != self._cached_values.get('DISCORD_ACTIVITY_NAME')
        )

        if changed:
            logger.info("🔄 Environment variable change detected!")
            self._cached_values = current_values.copy()

        return changed

    def __repr__(self):
        return f"Config(activity={self.DISCORD_ACTIVITY_NAME}, video_url={self.VIDEO_JSON_URL})"


# Global config instance
config = Config()
