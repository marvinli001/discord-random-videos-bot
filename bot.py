import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional

from config import config
from video_manager import VideoManager

logger = logging.getLogger(__name__)


class VideoBot(commands.Bot):
    """Discord bot for random video playback"""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )

        self.video_manager = VideoManager(config.VIDEO_JSON_URL)

    async def setup_hook(self):
        """Called when the bot is starting up"""
        # Fetch videos on startup
        success = await self.video_manager.fetch_videos()
        if not success:
            logger.error("Failed to fetch videos on startup")

        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f'Bot logged in as {self.user} (ID: {self.user.id})')

        # Set activity status
        activity = discord.Game(name=config.DISCORD_ACTIVITY_NAME)
        await self.change_presence(activity=activity)
        logger.info(f'Activity set to: {config.DISCORD_ACTIVITY_NAME}')


# Create bot instance
bot = VideoBot()


@bot.tree.command(name="randomvideo", description="获取一个随机视频")
async def randomvideo_slash(interaction: discord.Interaction):
    """Slash command for random video"""
    await send_random_video(interaction)


@bot.command(name="randomvideo")
async def randomvideo_text(ctx: commands.Context):
    """Text command for random video"""
    await send_random_video(ctx)


async def send_random_video(interaction_or_ctx):
    """Send a random video with next button"""
    # Defer the response if it's an interaction
    is_interaction = isinstance(interaction_or_ctx, discord.Interaction)

    if is_interaction:
        await interaction_or_ctx.response.defer()

    # Get next video
    video_url = bot.video_manager.get_next_video()

    if not video_url:
        error_msg = "❌ 无法获取视频，请稍后重试"
        if is_interaction:
            await interaction_or_ctx.followup.send(error_msg, ephemeral=True)
        else:
            await interaction_or_ctx.send(error_msg)
        return

    # Create message with video and button
    view = VideoView(video_url)
    content = create_video_message(video_url)

    if is_interaction:
        await interaction_or_ctx.followup.send(content=content, view=view)
    else:
        await interaction_or_ctx.send(content=content, view=view)


def create_video_message(video_url: str) -> str:
    """Create message content with filename and video URL for Discord embed"""
    filename = VideoManager.extract_filename(video_url)

    # Discord will automatically embed the video if we include the direct link
    # We display the filename and the URL separately so Discord can create the embed
    message = f"**📹 {filename}**\n{video_url}"

    return message


class VideoView(discord.ui.View):
    """View with Next button for getting another random video"""

    def __init__(self, current_video_url: str):
        super().__init__(timeout=None)  # No timeout
        self.current_video_url = current_video_url

    @discord.ui.button(label="下一个", style=discord.ButtonStyle.primary, emoji="⏭️")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle next button click"""
        await interaction.response.defer()

        # Get next video
        video_url = bot.video_manager.get_next_video()

        if not video_url:
            await interaction.followup.send("❌ 无法获取视频", ephemeral=True)
            return

        # Update the message with new video
        self.current_video_url = video_url
        content = create_video_message(video_url)

        # Create new view with updated video
        new_view = VideoView(video_url)

        try:
            # Edit the original message
            await interaction.message.edit(content=content, view=new_view)
        except Exception as e:
            logger.error(f"Failed to update message: {e}")
            await interaction.followup.send("❌ 更新失败", ephemeral=True)


@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        return

    logger.error(f"Command error: {error}")
    await ctx.send(f"❌ 发生错误: {str(error)}")


def run_bot():
    """Run the bot"""
    try:
        bot.run(config.DISCORD_BOT_TOKEN)
    except Exception as e:
        logger.error(f"Failed to run bot: {e}")
        raise
