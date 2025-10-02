# Discord Random Video Bot 🎬

A Discord bot that sends random videos from a JSON source with intelligent shuffle queue logic. Built for Railway deployment with hot-reload configuration support.

## Features ✨

- 🎲 **Smart Shuffle Queue**: Plays all videos once before repeating, ensuring variety
- 🔄 **Hot Reload**: Automatically reloads configuration changes
  - 💻 **Local**: Watches `.env` file for instant updates
  - ☁️ **Cloud**: Polls environment variables every 10 seconds
- 🎮 **Interactive UI**: Discord native embeds with "Next" button for seamless navigation
- 📱 **Multiple Interfaces**: Supports both slash commands (`/randomvideo`) and text commands (`randomvideo`)
- 🎯 **Auto-Embed**: Videos automatically embed in Discord's native player
- 🚀 **Railway Ready**: Designed for easy container deployment

## How It Works 🔧

1. **Video Queue**: Fetches video list from JSON URL and creates a shuffled queue
2. **No Repeats**: Ensures all videos play once before any video repeats
3. **Dynamic Cards**: Sends interactive messages with video embeds and "Next" button
4. **In-Place Updates**: Clicking "Next" updates the current message (no spam)
5. **Discord Embeds**: Discord automatically creates video player from direct URLs

## Setup 🚀

### Local Development

1. **Clone and Install**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**

   Create a `.env` file:
   ```env
   DISCORD_BOT_TOKEN=your_bot_token_here
   DISCORD_ACTIVITY_NAME=随机视频
   VIDEO_JSON_URL=https://videos.vistru.cn/videos.json
   ```

3. **Run the Bot**
   ```bash
   python main.py
   ```

### Railway Deployment

1. **Connect Repository**: Link your GitHub repo to Railway

2. **Set Environment Variables**:
   - `DISCORD_BOT_TOKEN`: Your Discord bot token
   - `DISCORD_ACTIVITY_NAME`: Bot activity status (default: "随机视频")
   - `VIDEO_JSON_URL`: JSON source URL (default: https://videos.vistru.cn/videos.json)

3. **Deploy**: Railway auto-detects Python and deploys automatically

## Configuration ⚙️

All settings are managed via environment variables:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DISCORD_BOT_TOKEN` | Discord bot token | - | ✅ Yes |
| `DISCORD_ACTIVITY_NAME` | Bot's activity status text | "随机视频" | ❌ No |
| `DISCORD_ACTIVITY_TYPE` | Activity type (playing/watching/listening/streaming/custom) | "watching" | ❌ No |
| `DISCORD_ACTIVITY_URL` | URL for streaming activity type | - | ❌ No |
| `VIDEO_JSON_URL` | Default video source JSON URL | https://videos.vistru.cn/videos.json | ❌ No |
| `STREAMABLE_JSON_URL` | Streamable video source JSON URL (for PC compatibility) | https://videos.vistru.cn/streamable.json | ❌ No |

### Video Sources 🎬

The bot supports multiple video sources that can be switched dynamically:

- **默认源 (Default Source)**: Main video collection from `VIDEO_JSON_URL`
- **Streamable源 (Streamable Source)**: PC-optimized videos from `STREAMABLE_JSON_URL`

Users can switch between sources using the "换源" button in the Discord interface.

### Activity Types 🎭

Choose from different Discord activity types:

| Type | Display Format | Example |
|------|----------------|---------|
| `playing` | 正在玩 {name} | "正在玩 随机视频" |
| `watching` | 观看 {name} | "观看 随机视频" ⭐ (default) |
| `listening` | 收听 {name} | "收听 随机视频" |
| `streaming` | 直播 {name} | "直播 随机视频" (requires `DISCORD_ACTIVITY_URL`) |
| `custom` | {name} | "随机视频" (custom status bubble) |

Set `DISCORD_ACTIVITY_TYPE` in your environment variables to change the display format.

### Hot Reload

The bot automatically detects configuration changes without restarting:

**Local Development (File Watcher)**
- 👁️ Watches `.env` file for changes
- ⚡ Instant reload when file is modified
- 🔧 Perfect for development

**Cloud Deployment (Environment Polling)**
- ☁️ Checks environment variables every 10 seconds
- 🔄 Auto-detects Railway/Heroku/Render environments
- 🎯 Updates bot activity and video source on change
- ✅ No restart needed - just update env vars in Railway dashboard!

## Usage 📖

### Commands

- **Slash Command**: `/randomvideo` - Get a random video
- **Text Command**: Type `randomvideo` in chat

### Interaction

1. Use command to get a random video
2. Bot sends message with:
   - Video filename (decoded from URL)
   - Embedded video player (Discord native)
   - "下一个 ⏭️" (Next) button
   - "换源 🔄" (Switch Source) button
3. Click "Next" button to load another random video from current source
4. Click "Switch Source" button to choose between:
   - **默认源 📹** - Default video source (VIDEO_JSON_URL)
   - **Streamable源 💻** - Streamable source for PC compatibility (STREAMABLE_JSON_URL)
5. Message updates in-place with new video

## Project Structure 📁

```
discord-random-videos-bot/
├── main.py              # Entry point with hot-reload watcher
├── bot.py              # Discord bot logic and commands
├── config.py           # Configuration management
├── video_manager.py    # Shuffle queue and video handling
├── requirements.txt    # Python dependencies
├── .env.example       # Example environment file
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

## Technical Details 🛠️

### Shuffle Queue Algorithm

1. Fetch all videos from JSON
2. Create shuffled queue from complete list
3. Serve videos sequentially from queue
4. When queue exhausted, create new shuffled queue
5. Repeat indefinitely

This ensures:
- ✅ All videos played before any repeat
- ✅ True randomness in each round
- ✅ No manual tracking needed

### Discord Integration

- Uses `discord.py` v2.3.2+
- Implements slash commands via app_commands
- Interactive UI with discord.ui.View and Buttons
- Message editing for in-place updates
- Automatic video embedding via direct URLs

## Dependencies 📦

- `discord.py` >= 2.3.2 - Discord API wrapper
- `python-dotenv` >= 1.0.0 - Environment variable management
- `aiohttp` >= 3.9.1 - Async HTTP requests
- `watchdog` >= 3.0.0 - File system monitoring for hot-reload

## Video JSON Format 📋

Expected JSON structure:
```json
[
  "https://videos.vistru.cn/video1.mp4",
  "https://videos.vistru.cn/video2.mp4",
  ...
]
```

Simple array of video URLs. The bot extracts and decodes filenames for display.

## Troubleshooting 🔍

**Bot not responding?**
- Check `DISCORD_BOT_TOKEN` is correct
- Ensure bot has proper permissions in Discord server
- Verify bot intents are enabled in Discord Developer Portal

**Videos not embedding?**
- Discord auto-embeds direct video URLs (.mp4, .webm, etc.)
- Ensure URLs are publicly accessible
- Check file size limits (Discord has upload limits)

**Hot reload not working?**
- Only works in local development
- Requires `.env` file to exist
- Railway uses environment variables (no hot-reload needed)

## License 📄

MIT License - Feel free to use and modify!

## Support 💬

For issues or questions, please open an issue on GitHub.

---

Made with ❤️ for Discord communities
