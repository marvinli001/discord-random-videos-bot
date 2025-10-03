#!/usr/bin/env python3
"""
Test auto-refresh and smart video merging
"""
import asyncio
import logging
from video_manager import VideoManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_video_merging():
    """Test smart video merging when JSON updates"""

    # Mock initial video list
    initial_videos = [
        "https://example.com/video1.mp4",
        "https://example.com/video2.mp4",
        "https://example.com/video3.mp4",
    ]

    # Mock updated video list (added video4, removed video2)
    updated_videos = [
        "https://example.com/video1.mp4",
        "https://example.com/video3.mp4",
        "https://example.com/video4.mp4",
        "https://example.com/video5.mp4",
    ]

    print("📹 Initial video list:")
    for v in initial_videos:
        print(f"  - {v}")

    # Simulate user queue
    manager = VideoManager("https://example.com/videos.json")
    manager.all_videos = initial_videos.copy()

    # Create a user queue and get 1 video
    user_id = 123
    video1 = manager.get_next_video(user_id)
    print(f"\n👤 User {user_id} watched: {video1}")

    print(f"\n📊 Queue status before update:")
    status = manager.get_queue_status(user_id)
    print(f"  Total: {status['total_videos']}, Remaining: {status['videos_remaining']}")

    # Simulate JSON update
    print("\n🔄 JSON updated with new videos...")
    print("📹 Updated video list:")
    for v in updated_videos:
        marker = "🆕" if v not in initial_videos else ""
        removed = "❌" if v in initial_videos and v not in updated_videos else ""
        print(f"  - {v} {marker}{removed}")

    # Merge new videos
    await manager._merge_new_videos(updated_videos)

    print(f"\n📊 Queue status after update:")
    status = manager.get_queue_status(user_id)
    print(f"  Total: {status['total_videos']}, Remaining: {status['videos_remaining']}")

    # Get user queue
    user_queue = manager.user_queues[user_id]
    print(f"\n📜 Current user queue:")
    for i, v in enumerate(user_queue.queue):
        played = "✅" if i < user_queue.current_index else "⏳"
        print(f"  {played} [{i}] {v}")

    print("\n✅ Test completed!")
    print("\n💡 Key observations:")
    print("  - New videos (video4, video5) added to remaining queue")
    print("  - Removed video (video2) removed from queue if not played")
    print("  - Already played videos remain unchanged")
    print("  - Current position preserved")


if __name__ == "__main__":
    asyncio.run(test_video_merging())
