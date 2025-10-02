#!/usr/bin/env python3
"""
Discord Random Video Bot
A bot that sends random videos from a JSON source with shuffle queue logic
"""

import asyncio
import logging
import sys
import signal
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from config import config
from bot import run_bot, bot

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Detect if running in cloud environment
IS_CLOUD = os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('HEROKU_APP_NAME') or os.getenv('RENDER')


class EnvFileHandler(FileSystemEventHandler):
    """Monitor .env file for changes and trigger reload"""

    def __init__(self, loop):
        self.loop = loop
        self.last_modified = 0

    def on_modified(self, event):
        if event.src_path.endswith('.env'):
            # Debounce: prevent multiple rapid reloads
            import time
            current_time = time.time()
            if current_time - self.last_modified < 1:
                return

            self.last_modified = current_time
            logger.info("📝 .env file changed, reloading configuration...")

            # Schedule reload in the bot's event loop
            asyncio.run_coroutine_threadsafe(self.reload_config(), self.loop)

    async def reload_config(self):
        """Reload configuration and update bot"""
        try:
            # Reload config
            config.reload()

            # Update bot activity
            if bot.user:
                activity = discord.Game(name=config.DISCORD_ACTIVITY_NAME)
                await bot.change_presence(activity=activity)
                logger.info(f"✅ Configuration reloaded - Activity: {config.DISCORD_ACTIVITY_NAME}")

            # Update video manager URL
            bot.video_manager.json_url = config.VIDEO_JSON_URL
            await bot.video_manager.fetch_videos()
            logger.info(f"✅ Video source updated: {config.VIDEO_JSON_URL}")

        except Exception as e:
            logger.error(f"❌ Failed to reload configuration: {e}")


def setup_env_watcher(loop):
    """Setup file watcher for .env file hot reload (local only)"""
    env_path = Path('.env')

    if not env_path.exists():
        logger.warning("⚠️  .env file not found, file watcher disabled")
        return None

    event_handler = EnvFileHandler(loop)
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()

    logger.info("👁️  Watching .env file for changes (local hot reload enabled)")
    return observer


async def cloud_env_monitor():
    """Monitor environment variables for changes (cloud deployment)"""
    logger.info("☁️  Cloud environment detected - polling for env variable changes")

    import discord

    while True:
        try:
            await asyncio.sleep(10)  # Check every 10 seconds

            if config.has_changed():
                logger.info("🔄 Environment variables changed, reloading...")

                # Reload config
                config.reload()

                # Update bot activity
                if bot.user:
                    activity = discord.Game(name=config.DISCORD_ACTIVITY_NAME)
                    await bot.change_presence(activity=activity)
                    logger.info(f"✅ Bot activity updated: {config.DISCORD_ACTIVITY_NAME}")

                # Update video manager
                bot.video_manager.json_url = config.VIDEO_JSON_URL
                await bot.video_manager.fetch_videos()
                logger.info(f"✅ Video source updated: {config.VIDEO_JSON_URL}")

        except Exception as e:
            logger.error(f"❌ Error in cloud env monitor: {e}")


async def run_bot_async():
    """Run bot asynchronously with cloud monitoring"""
    # Start cloud env monitor if in cloud
    if IS_CLOUD:
        asyncio.create_task(cloud_env_monitor())

    # Run bot
    async with bot:
        await bot.start(config.DISCORD_BOT_TOKEN)


def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("🛑 Shutting down bot...")
    sys.exit(0)


def main():
    """Main entry point"""
    logger.info("🚀 Starting Discord Random Video Bot")
    logger.info(f"📋 {config}")
    logger.info(f"🌍 Environment: {'Cloud' if IS_CLOUD else 'Local'}")

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    observer = None

    try:
        if IS_CLOUD:
            # Cloud deployment: use async monitoring
            logger.info("☁️  Starting with cloud environment variable monitoring...")
            asyncio.run(run_bot_async())
        else:
            # Local deployment: use file watcher
            logger.info("💻 Starting with local .env file watcher...")

            # Get event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Setup .env file watcher
            observer = setup_env_watcher(loop)

            # Run bot with traditional method
            run_bot()

    except KeyboardInterrupt:
        logger.info("🛑 Received keyboard interrupt")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if observer:
            observer.stop()
            observer.join()
        logger.info("👋 Bot stopped")


if __name__ == "__main__":
    main()
