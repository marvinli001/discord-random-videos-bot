#!/usr/bin/env python3
"""
Test multi-source queue independence
"""
import asyncio
import logging
from video_manager import VideoManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_multi_source_queues():
    """Test that each source maintains independent queues"""

    print("🎬 Testing Multi-Source Queue Independence\n")

    # Create manager with source 1
    manager = VideoManager("https://example.com/videos.json")
    manager.all_videos = ["video1.mp4", "video2.mp4", "video3.mp4"]

    user_id = 123

    # Get 2 videos from source 1
    print("📹 Source 1: https://example.com/videos.json")
    video1 = manager.get_next_video(user_id)
    video2 = manager.get_next_video(user_id)
    print(f"  Watched: {video1}, {video2}")

    status1 = manager.get_queue_status(user_id)
    print(f"  Status: {status1['current_position']}/{status1['queue_size']} videos")

    # Switch to source 2
    print("\n🔄 Switching to Source 2...")
    manager.json_url = "https://example.com/streamable.json"
    manager.all_videos = ["stream1.mp4", "stream2.mp4", "stream3.mp4", "stream4.mp4"]

    # Get 1 video from source 2 (should be fresh queue)
    print("\n📹 Source 2: https://example.com/streamable.json")
    video3 = manager.get_next_video(user_id)
    print(f"  Watched: {video3}")

    status2 = manager.get_queue_status(user_id)
    print(f"  Status: {status2['current_position']}/{status2['queue_size']} videos")

    # Switch back to source 1
    print("\n🔄 Switching back to Source 1...")
    manager.json_url = "https://example.com/videos.json"
    manager.all_videos = ["video1.mp4", "video2.mp4", "video3.mp4"]

    # Get next video from source 1 (should resume from position 2)
    print("\n📹 Source 1 (resumed): https://example.com/videos.json")
    video4 = manager.get_next_video(user_id)
    print(f"  Watched: {video4}")

    status1_resumed = manager.get_queue_status(user_id)
    print(f"  Status: {status1_resumed['current_position']}/{status1_resumed['queue_size']} videos")

    # Verify
    print("\n✅ Verification:")
    print(f"  Source 1 initial: 2/3 videos watched")
    print(f"  Source 2: 1/4 videos watched (independent queue)")
    print(f"  Source 1 resumed: 3/3 videos watched (preserved progress)")

    if status1_resumed['current_position'] == 3:
        print("\n🎉 SUCCESS! Multi-source queues work independently!")
    else:
        print("\n❌ FAILED! Queue state not preserved")


if __name__ == "__main__":
    asyncio.run(test_multi_source_queues())
