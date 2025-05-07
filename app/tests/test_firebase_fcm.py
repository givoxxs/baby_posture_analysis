from app.services.notification_service import send_fcm_notification
import logging
import asyncio
import os
from pathlib import Path

# Configure logging to show on console
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("firebase_test")

# Find the root directory and set credential path
ROOT_DIR = Path(__file__).parent.parent.parent
CREDENTIAL_PATH = os.path.join(ROOT_DIR, "firebase-credentials.json")


async def test_fcm_notification():
    """Test sending a simple FCM notification"""
    logger.info("Testing FCM notification...")

    # Test data - replace with a valid FCM token from your application
    test_token = "eJR67MaVToiRzpUnqflHug:APA91bHWVc4TbmESAYUj3_HtSFo4iNfmMTHHt8Q7As5MSI6KsQtIP1mxu9-cN6juBAlvL-XqQVibNpor6MNoQOZEKdq_6HuznwbK9kqTBetMoEl4vst7jOc"  # Replace with a valid token from your device

    # Create message in the format expected by your notification_service
    message = {
        "title": "Test Notification",
        "body": "This is a test notification",
        "data": {
            "id": "test-notification-id",
            "type": "test",
            "time": "2023-10-01T12:00:00Z",
            "duration": "0",
        },
    }

    # Send test notification
    result = await send_fcm_notification(test_token, message)

    if result:
        logger.info("✅ SUCCESS: FCM notification sent successfully")
        return True
    else:
        logger.error("❌ FAILED: Could not send FCM notification")
        return False


if __name__ == "__main__":
    # Import here to prevent circular imports
    from datetime import datetime
    from firebase_admin import credentials, initialize_app

    # Run the Firebase connection test
    connection_success = False
    try:
        # Check if Firebase is already initialized
        try:
            from firebase_admin import get_app

            app = get_app()
            logger.info("Firebase app already initialized")
            connection_success = True
        except:
            # Initialize Firebase if not already done
            logger.info(f"Initializing Firebase with credentials at: {CREDENTIAL_PATH}")
            cred = credentials.Certificate(CREDENTIAL_PATH)
            initialize_app(cred)
            connection_success = True
            logger.info("Firebase connection established successfully")
    except Exception as e:
        logger.error(f"Error connecting to Firebase: {e}")

    # Run the FCM notification test
    if connection_success:
        fcm_success = asyncio.run(test_fcm_notification())
    else:
        fcm_success = False

    # Show the final results
    print("\n" + "=" * 50)
    if connection_success:
        print("✅ Firebase connection test: SUCCESS")
        print(f"Firebase credentials file was found at: {CREDENTIAL_PATH}")
        print("Firebase connection was established successfully.")
    else:
        print("❌ Firebase connection test: FAILED")
        print("Please check the following:")
        print(f"1. Firebase credentials file exists at: {CREDENTIAL_PATH}")
        print(
            "2. The credentials file contains valid Firebase service account information"
        )
        print("3. The Firebase project is properly set up and accessible")

    if fcm_success:
        print("\n✅ FCM notification test: SUCCESS")
        print("Test notification was sent successfully")
    else:
        print("\n❌ FCM notification test: FAILED")
        print("Could not send test notification")
        print("Make sure to replace 'YOUR_VALID_FCM_TOKEN' with an actual device token")
    print("=" * 50)
