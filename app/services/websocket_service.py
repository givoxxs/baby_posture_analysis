import json
import asyncio
import base64
import time
from datetime import datetime
import cloudinary.uploader
from app.config import db
from app.services.analysis_service import get_singleton_analysis_service

analyze_service = get_singleton_analysis_service()


class DeviceState:
    def __init__(self, device_id, thresholds):
        self.device_id = device_id
        self.side_threshold = thresholds.get("sideThreshold", 10)
        self.prone_threshold = thresholds.get("proneThreshold", 10)
        self.no_blanket_threshold = thresholds.get("noBlanketThreshold", 10)
        self.max_history = 5
        self.position_baby = {
            "position": "",
            "count": 0,
            "first_time": None,
            "last_time": None,
        }
        self.blanket_baby = {
            "is_covered": False,
            "count": 0,
            "first_time": None,
            "last_time": None,
        }
        self.posture_history = []

        self.last_notification_time = {"noBlanket": None, "side": None, "prone": None}

    async def update_position_baby(self, position, timestamp):
        if self.position_baby["position"] == position:
            self.position_baby["count"] += 1
            self.position_baby["last_time"] = timestamp
        else:
            self.position_baby["position"] = position
            self.position_baby["count"] = 1
            self.position_baby["first_time"] = timestamp
            self.position_baby["last_time"] = timestamp
            await send_event_to_firestore(self.device_id, position, timestamp)

    async def update_blanket_baby(self, is_covered, timestamp):
        if self.blanket_baby["is_covered"] == is_covered:
            self.blanket_baby["count"] += 1
            self.blanket_baby["last_time"] = timestamp
        else:
            self.blanket_baby["is_covered"] = is_covered
            self.blanket_baby["count"] = 1
            self.blanket_baby["last_time"] = timestamp
            if is_covered == False:
                await send_event_to_firestore(self.device_id, "no_blanket", timestamp)
            else:
                await send_event_to_firestore(self.device_id, "has_blanket", timestamp)

    # tính số giây giữa 2 thời điểm
    def calc_time(self, start_time, end_time):
        if start_time is None or end_time is None:
            return 0
        start_time = datetime.fromisoformat(start_time)
        end_time = datetime.fromisoformat(end_time)
        res = (end_time - start_time).total_seconds()
        # ép kiểu về số nguyên
        return int(res)

    def check_position_baby(self):
        if self.position_baby["position"] == "side":
            if (
                self.position_baby["count"] >= self.side_threshold
                and self.position_baby["last_time"] is not None
                and self.calc_time(
                    self.position_baby["first_time"], self.position_baby["last_time"]
                )
                > (self.side_threshold * 90 / 100)
            ):
                return True
            else:
                return False
        elif self.position_baby["position"] == "prone":
            if (
                self.position_baby["count"] >= self.prone_threshold
                and self.position_baby["last_time"] is not None
                and self.calc_time(
                    self.position_baby["first_time"], self.position_baby["last_time"]
                )
                > (self.prone_threshold * 90 / 100)
            ):
                return True
            else:
                return False

    def check_blanket_baby(self):
        if self.blanket_baby["is_covered"] == False:
            if (
                self.blanket_baby["count"] >= self.no_blanket_threshold
                and self.blanket_baby["last_time"] is not None
                and self.calc_time(
                    self.blanket_baby["first_time"], self.blanket_baby["last_time"]
                )
                > (self.no_blanket_threshold * 90 / 100)
            ):
                return True
            else:
                return False
        else:
            return False


async def get_device_thresholds(device_id):
    try:
        # Create query
        query = db.collection("devices").where("id", "==", device_id)
        print(f"Querying device thresholds for ID: {device_id}")
        print(f"Query: {query}")
        # Execute query and get results
        device_docs = await query.get()
        print(f"Device documents found: {len(device_docs)}")
        print(
            f"Device documents: {device_docs[0].to_dict() if device_docs else 'No documents'}"
        )
        # Check results
        if not device_docs or len(device_docs) == 0:
            print(f"No device found with ID: {device_id}")
            return None
        # Convert first document to dict
        return device_docs[0].to_dict()
    except Exception as e:
        print(f"Error getting device thresholds: {e}")
        return None


async def upload_to_cloudinary(image_base64):
    try:
        result = cloudinary.uploader.upload(f"data:image/jpeg;base64,{image_base64}")
        return result["secure_url"]
    except Exception as e:
        print(f"Error uploading to Cloudinary: {e}")
        return None


async def send_event_to_firestore(device_id, event_type, start_time):
    try:
        event = {"deviceId": device_id, "type": event_type, "time": start_time}
        await db.collection("devices").document(device_id).collection("events").add(
            event
        )
        print(f"Event sent to Firestore: {event}")
    except Exception as e:
        print(f"Error sending event to Firestore: {e}")


async def send_notifications(
    device_id, event_type, duration, start_time, image_url=None
):
    # Send to PushNotification collection
    push_notification = {
        "deviceId": device_id,
        "type": event_type,
        "duration": duration,
        "time": start_time,
    }
    await db.collection("devices").document(device_id).collection(
        "pushnotifications"
    ).add(push_notification)

    # Send to Notification collection with image
    if image_url:
        notification = {
            "deviceId": device_id,
            "type": event_type,
            "duration": duration,
            "time": start_time,
            "imageUrl": image_url,
        }
        await db.collection("notifications").add(notification)


class WebSocketHandler:
    def __init__(self):
        self.devices = {}

    async def handle_connection(self, websocket):
        device_id = None
        try:
            # First message should be device ID
            device_id = await websocket.receive_text()
            print(f"Device connected with ID: {device_id}")

            # Get device thresholds from Firebase
            thresholds = await get_device_thresholds(device_id)
            if not thresholds:
                await websocket.close()
                return

            # Initialize device state
            device_state = DeviceState(device_id, thresholds)
            self.devices[device_id] = device_state

            while True:
                data = await websocket.receive_json()

                # Extract image and timestamp
                image_base64 = data.get("image_base64")
                timestamp = data.get("timestamp")
                print(f"timestamp: {timestamp}")

                if not image_base64 or not timestamp:
                    continue

                # Analyze image
                analysis_result = await analyze_service.analyze_image_base64(
                    image_base64
                )
                print(f"Image analysis result: {analysis_result.get('success')}")
                if analysis_result.get("success") is False:
                    print(f"Image analysis failed: {analysis_result.get('message')}")
                    continue

                posture = analysis_result.get("analysis", {}).get("position")
                print(f"Posture detected: {posture}")
                if not posture:
                    print("No posture detected in the image.")
                    continue

                if posture == "Nằm ngửa":
                    posture = "back"
                elif posture == "Nằm sấp":
                    posture = "prone"
                elif posture == "Nằm nghiêng":
                    posture = "side"
                else:
                    posture = "unknown"

                if posture == "unknown":
                    print("Unknown posture detected.")
                    continue

                # Kiểm tra xem key 'blanket' có tồn tại trong analysis_result hay không
                if "blanket" not in analysis_result:
                    print("Error: 'blanket' key is missing in analysis_result")
                    has_blanket = False
                    # continue

                blanket_data = analysis_result["blanket"]

                # Kiểm tra xem blanket_data có phải là một dictionary hay không
                if not isinstance(blanket_data, dict):
                    print("Error: 'blanket' data is not a dictionary")
                    has_blanket = False
                    # continue

                has_blanket = blanket_data.get("is_covered", False)
                print(f"Blanket status: {has_blanket}")

                # Update posture history
                device_state.posture_history.append(
                    {
                        "posture": posture,
                        "has_blanket": has_blanket,
                        "timestamp": timestamp,
                    }
                )

                if len(device_state.posture_history) > device_state.max_history:
                    device_state.posture_history.pop(0)

                # Update blanket history
                if len(device_state.posture_history) < device_state.max_history:
                    await device_state.update_position_baby(posture, timestamp)
                else:
                    # check xem có đủ 3 posture trong max_history không, chỉ cần có 3 posture là đủ
                    side_count = sum(
                        1
                        for p in device_state.posture_history
                        if p["posture"] == posture
                    )
                    if side_count >= 3:
                        await device_state.update_position_baby(posture, timestamp)

                # Update blanket status
                if len(device_state.posture_history) < device_state.max_history:
                    await device_state.update_blanket_baby(has_blanket, timestamp)
                else:
                    # check xem có đủ 3 blanket trong max_history không, chỉ cần có 3 blanket là đủ
                    blanket_count = sum(
                        1
                        for p in device_state.posture_history
                        if p["has_blanket"] == has_blanket
                    )
                    if blanket_count >= 3:
                        await device_state.update_blanket_baby(has_blanket, timestamp)

                check_position = device_state.check_position_baby()
                if check_position:
                    now_position = device_state.position_baby["position"]
                    if (
                        device_state.last_notification_time[now_position] is None
                        or device_state.calc_time(
                            device_state.last_notification_time[now_position], timestamp
                        )
                        > 10
                    ):
                        device_state.last_notification_time[now_position] = timestamp
                        image_url = await upload_to_cloudinary(image_base64)
                        await send_notifications(
                            device_id,
                            now_position,
                            device_state.position_baby["count"],
                            timestamp,
                            image_url,
                        )
                        print(f"Notification sent for {now_position} position.")

                # check_blanket = device_state.check_blanket_baby()
                # if check_blanket is False:
                #     if device_state.last_notification_time['noBlanket'] is None or device_state.calc_time(device_state.last_notification_time['noBlanket'], timestamp) > 10:
                #         device_state.last_notification_time['noBlanket'] = timestamp
                #         image_url = await upload_to_cloudinary(image_base64)
                #         await send_notifications(device_id, 'noBlanket', device_state.blanket_baby['count'], timestamp, image_url)
                #         print(f"Notification sent for no blanket.")
        except Exception as e:
            print(f"Error in WebSocket connection: {e}")
        finally:
            try:
                if device_id is not None and device_id in self.devices:
                    del self.devices[device_id]
                    print(
                        f"Device {device_id} disconnected and removed from active devices"
                    )
            except Exception as cleanup_error:
                print(f"Error during cleanup for device {device_id}: {cleanup_error}")
