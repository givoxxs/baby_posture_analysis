import json
import cloudinary.uploader
import firebase_admin
from firebase_admin import messaging
from datetime import datetime, timedelta, timezone
from app.config import db
from google.cloud.firestore_v1.base_query import FieldFilter
import logging

logger = logging.getLogger(__name__)

# ...existing code...


def convert_to_vietnam_timezone(timestamp):
    """
    Convert a timestamp to Vietnam timezone (UTC+7)

    Args:
        timestamp: A datetime object or ISO format string

    Returns:
        datetime: A datetime object in Vietnam timezone (UTC+7)
    """
    try:
        if isinstance(timestamp, str):
            # Convert ISO string to datetime object
            timestamp = datetime.fromisoformat(timestamp)

        # If timestamp has no timezone info, assume it's UTC
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        # Convert to Vietnam timezone (UTC+7)
        vietnam_tz = timezone(timedelta(hours=7))
        vietnam_time = timestamp.astimezone(vietnam_tz)

        logger.info(f"Converted time to Vietnam timezone: {vietnam_time}")
        return vietnam_time
    except Exception as e:
        logger.error(f"Error converting to Vietnam timezone: {e}")
        return timestamp  # Return original timestamp if conversion fails


async def upload_to_cloudinary(image_base64):
    """Upload image to Cloudinary and return the URL"""
    try:
        result = cloudinary.uploader.upload(f"data:image/jpeg;base64,{image_base64}")
        logger.info(f"Image uploaded to Cloudinary: {result['secure_url']}")
        return result["secure_url"]
    except Exception as e:
        logger.error(f"Error uploading to Cloudinary: {e}")
        return None


async def send_event_to_firestore(device_id, event_type, start_time):
    """Record an event in the device's events collection"""
    try:
        if isinstance(start_time, str):
            start_time = convert_to_vietnam_timezone(start_time)
            logger.info(f"Converted start_time to Firestore timestamp: {start_time}")
        event = {"deviceId": device_id, "type": event_type, "time": start_time}
        await db.collection("devices").document(device_id).collection("events").add(
            event
        )
        logger.info(f"Event sent to Firestore: {event}")
    except Exception as e:
        logger.error(f"Error sending event to Firestore: {e}")


async def get_device_connections(device_id):
    """Get all connections for a device"""
    try:
        connections_ref = db.collection("connections").where(
            # "deviceId", "==", device_id
            filter=FieldFilter("deviceId", "==", device_id)
        )
        connections = await connections_ref.get()
        print(f"Retrieved connections for device {device_id}: {connections}")
        return [connection.to_dict() for connection in connections]
    except Exception as e:
        logger.error(f"Error getting device connections: {e}")
        return []


async def get_user(user_id):
    """Get user document by ID"""
    try:
        # user_query = db.collection("users").where("id", "==", user_id)
        user_query = db.collection("users").where(
            filter=FieldFilter("id", "==", user_id)
        )
        user_doc = await user_query.get()
        if user_doc:
            return user_doc[0].to_dict()

        logger.warning(f"No user found with ID: {user_id}")
        return None
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return None


async def send_notifications(
    device_id, event_type, duration, start_time, image_url=None
):
    """
    Send notifications to all users connected to a device

    Args:
        device_id: The device ID
        event_type: The type of event (side, prone, no_blanket, etc.)
        duration: Duration of the event in seconds
        start_time: The timestamp of when the event started
        image_url: Optional URL to an image
    """
    try:
        firestore_timestamp = start_time
        unix_timestamp = 0

        if isinstance(start_time, str):
            firestore_timestamp = datetime.fromisoformat(start_time)
            # Convert to Vietnam timezone
            firestore_timestamp = convert_to_vietnam_timezone(firestore_timestamp)
        elif isinstance(start_time, datetime):
            firestore_timestamp = start_time
            # Convert to Vietnam timezone
            firestore_timestamp = convert_to_vietnam_timezone(firestore_timestamp)
        elif isinstance(start_time, int):
            # If it's already a Unix timestamp
            firestore_timestamp = convert_to_vietnam_timezone(
                datetime.fromtimestamp(start_time)
            )

        # Map event types to notification types
        notification_type_map = {
            "side": "Side",
            "prone": "Prone",
            "no_blanket": "NoBlanket",
            "has_blanket": "Blanket",
        }

        old_notification_type = event_type

        # Get notification type for the event
        notification_type = notification_type_map.get(event_type, event_type)

        # Save to global notifications collection with image URL if available
        if image_url:
            notification = {
                "type": old_notification_type,
                "duration": duration,
                "time": firestore_timestamp,
                "imageUrl": image_url,
            }

            update_time, doc_ref = (
                await db.collection("devices")
                .document(device_id)
                .collection("notifications")
                .add(notification)
            )
            notification_id = doc_ref.id

            # Get all connections for this device
            connections = await get_device_connections(device_id)

            # For each connection, get the user and send notification to their FCM tokens
            for connection in connections:
                user_id = connection.get("userId")
                print(f"User ID: {user_id}")
                if not user_id:
                    continue

                # Get the user document to check language preference and FCM tokens
                user = await get_user(user_id)
                if not user or not user.get("fcmTokens"):
                    continue

                # Determine language preference (default to 'en' if not specified)
                language = user.get("language", "en")

                # Create notification title and body based on language preference
                title, body = create_notification_content(
                    language,
                    connection.get("name", "Device"),
                    notification_type,
                    duration,
                )

                fcm_message_data = {
                    "id": str(notification_id),
                    "type": str(old_notification_type),
                    "time": str(start_time),
                    "duration": str(duration),
                }

                # Create the FCM message payload
                fcm_message = {
                    "title": title,
                    "body": body,
                    "data": fcm_message_data,
                }

                # Send to all FCM tokens for this user
                fcm_tokens = user.get("fcmTokens", [])
                for token in fcm_tokens:
                    await send_fcm_notification(token, fcm_message)

    except Exception as e:
        logger.error(f"Error sending notifications: {e}")


def create_notification_content(language, device_name, notification_type, duration):
    """
    Create notification title and body based on language preference

    Args:
        language: User language preference ('en' or 'vi')
        device_name: Name of the device/connection
        notification_type: Type of notification (Side, Prone, NoBlanket, etc.)
        duration: Duration in seconds

    Returns:
        Tuple of (title, body)
    """
    if language == "vi":
        title_map = {
            "Side": f"[{device_name}] Cảnh báo nằm nghiêng",
            "Prone": f"[{device_name}] Cảnh báo nằm sấp",
            "NoBlanket": f"[{device_name}] Cảnh báo không có chăn",
            "Blanket": f"[{device_name}] Thông báo có chăn",
            "Crying": f"[{device_name}] Cảnh báo khóc",
        }

        body_map = {
            "Side": f"Bé đang nằm nghiêng, đã liên tục trong {duration} giây",
            "Prone": f"Bé đang nằm sấp, đã liên tục trong {duration} giây",
            "NoBlanket": f"Bé không có chăn, đã liên tục trong {duration} giây",
            "Blanket": f"Bé đã được đắp chăn",
            "Crying": f"Bé đang khóc, đã liên tục trong {duration} giây",
        }
    else:  # Default to English
        title_map = {
            "Side": f"[{device_name}] Side position alert",
            "Prone": f"[{device_name}] Prone position alert",
            "NoBlanket": f"[{device_name}] No blanket alert",
            "Blanket": f"[{device_name}] Blanket notification",
            "Crying": f"[{device_name}] Crying alert",
        }

        body_map = {
            "Side": f"Baby is lying on his side, continuously for {duration} seconds",
            "Prone": f"Baby is lying on his stomach, continuously for {duration} seconds",
            "NoBlanket": f"Baby has no blanket, continuously for {duration} seconds",
            "Blanket": f"Baby is now covered with a blanket",
            "Crying": f"Baby is crying, continuously for {duration} seconds",
        }

    # Get the title and body or use defaults if the type is not in the map
    title = title_map.get(notification_type, f"[{device_name}] Alert")
    body = body_map.get(
        notification_type, f"Alert condition detected for {duration} seconds"
    )

    return title, body


async def send_fcm_notification(token, message):
    """
    Send a notification to a specific FCM token
    """
    try:
        # Create the FCM message
        fcm_message = messaging.Message(
            notification=messaging.Notification(
                title=message["title"], body=message["body"]
            ),
            data=message["data"],
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    priority="high",
                    channel_id="babycare-alerts",
                ),
            ),
            token=token,
        )

        # Send the message
        response = messaging.send(fcm_message)
        logger.info(f"Successfully sent FCM message to {token}: {response}")
        return response
    except Exception as e:
        logger.error(f"Error sending FCM notification: {e}")
        return None


async def get_device_thresholds(device_id):
    """Get device thresholds from Firestore"""
    try:
        # Create query
        device_doc = await db.collection("devices").document(device_id).get()
        logger.info(f"Querying device thresholds for ID: {device_id}")

        # Check results
        if not device_doc.exists:
            logger.warning(f"No device found with ID: {device_id}")
            return {
                "sideThreshold": 10,
                "proneThreshold": 10,
                "noBlanketThreshold": 10,
            }  # Default values

        # Convert document to dict
        device_data = device_doc.to_dict()
        thresholds = {
            "sideThreshold": device_data.get("sideThreshold", 10),
            "proneThreshold": device_data.get("proneThreshold", 10),
            "noBlanketThreshold": device_data.get("noBlanketThreshold", 100),
        }
        logger.info(f"Retrieved thresholds for device {device_id}: {thresholds}")
        return thresholds
    except Exception as e:
        logger.error(f"Error getting device thresholds: {e}")
        return {
            "sideThreshold": 10,
            "proneThreshold": 10,
            "noBlanketThreshold": 10,
        }  # Default values in case of error


def setup_device_thresholds_listener(device_id, callback):
    """
    Set up a real-time listener for threshold changes in Firestore

    Args:
        device_id: The device ID to monitor
        callback: Function to call when thresholds are updated
                  Function signature: callback(thresholds_dict)

    Returns:
        Firestore listener object that can be used to unsubscribe
    """
    try:
        # Get reference to the device document
        doc_ref = db.collection("devices").document(device_id)

        # Define callback function for the listener
        def on_snapshot(doc_snapshot, changes, read_time):
            try:
                # For document listener, doc_snapshot is the document itself, not a list
                if doc_snapshot.exists:
                    device_data = doc_snapshot.to_dict()
                    thresholds = {
                        "sideThreshold": device_data.get("sideThreshold", 10),
                        "proneThreshold": device_data.get("proneThreshold", 10),
                        "noBlanketThreshold": device_data.get(
                            "noBlanketThreshold", 100
                        ),
                    }
                    logger.info(
                        f"Thresholds updated for device {device_id}: {thresholds}"
                    )
                    # Call the provided callback with the new thresholds
                    callback(thresholds)
            except Exception as e:
                logger.error(f"Error in threshold listener callback: {e}")

        # Set up the listener
        return doc_ref.on_snapshot(on_snapshot)
    except Exception as e:
        logger.error(f"Error setting up threshold listener: {e}")
        return None
