from app.services.notification_service import send_notifications
import logging

logger = logging.getLogger(__name__)

DEVICE_ID_TEST = "18ff6551-820b-4aad-b714-1143629970f0"


async def test_send_notifications():
    """Test sending notifications to a device"""
    logger.info("Testing send_notifications...")
    print("Testing send_notifications...")
    try:
        await send_notifications(
            DEVICE_ID_TEST,
            event_type="side",
            duration=50,
            start_time="2023-10-01T12:00:00Z",
            image_url="https://sankid.vn/wp-content/uploads/2024/05/anh-be-trai-khau-khinh-8.jpg",
        )
        logger.info("✅ SUCCESS: Notifications sent successfully")
        print("Notifications sent successfully")
        return True
    except Exception as e:
        logger.error(f"❌ FAILED: Could not send notifications - {e}")
        print(f"Could not send notifications - {e}")
        return False


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_send_notifications())
