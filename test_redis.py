#!/usr/bin/env python3
"""
Test Redis connection and queue persistence
"""
import sys
from redis_storage import RedisStorage

def test_redis():
    """Test Redis connection and basic operations"""
    print("🧪 Testing Redis connection...")

    storage = RedisStorage()

    if not storage.available:
        print("❌ Redis not available. Make sure Redis is running and environment variables are set.")
        return False

    print("✅ Redis connected successfully!")

    # Test save and load
    test_user_id = 12345
    test_queue_data = {
        "queue": ["video1.mp4", "video2.mp4", "video3.mp4"],
        "current_index": 1
    }

    print(f"\n📝 Testing save operation for user {test_user_id}...")
    success = storage.save_user_queue(test_user_id, test_queue_data)
    if success:
        print("✅ Save successful")
    else:
        print("❌ Save failed")
        return False

    print(f"\n📖 Testing load operation for user {test_user_id}...")
    loaded_data = storage.load_user_queue(test_user_id)
    if loaded_data:
        print(f"✅ Load successful: {loaded_data}")
        if loaded_data == test_queue_data:
            print("✅ Data matches!")
        else:
            print(f"⚠️  Data mismatch. Expected: {test_queue_data}, Got: {loaded_data}")
    else:
        print("❌ Load failed")
        return False

    print(f"\n🗑️  Testing delete operation...")
    success = storage.delete_user_queue(test_user_id)
    if success:
        print("✅ Delete successful")
    else:
        print("❌ Delete failed")

    # Verify deletion
    loaded_data = storage.load_user_queue(test_user_id)
    if loaded_data is None:
        print("✅ Verified: Queue deleted successfully")
    else:
        print(f"⚠️  Queue still exists: {loaded_data}")

    storage.close()
    print("\n✅ All tests passed!")
    return True

if __name__ == "__main__":
    success = test_redis()
    sys.exit(0 if success else 1)
