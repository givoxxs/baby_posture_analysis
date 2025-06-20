from typing import Dict, Any
from app.config import db
from fastapi import WebSocket, WebSocketDisconnect
from app.services.analysis_service import get_singleton_analysis_service
from app.services.device_state import DeviceState
from app.services.notification_service import (
    get_device_thresholds,
    upload_to_cloudinary,
    send_notifications,
    test_device_connection,
)
from app.services.firebase_threshold_listener import get_threshold_listener
import logging

logger = logging.getLogger(__name__)

analyze_service = get_singleton_analysis_service()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, device_id: str):
        await websocket.accept()
        self.active_connections[device_id] = websocket
        logger.info(f"Device {device_id} connected")

    def disconnect(self, device_id: str):
        if device_id in self.active_connections:
            del self.active_connections[device_id]
        # logger.info(f"Device {device_id} disconnected")

    async def send_message(self, device_id: str, message: Dict[str, Any]):
        if device_id in self.active_connections:
            await self.active_connections[device_id].send_json(message)


class WebSocketHandler:
    def __init__(self):
        self.devices = {}
        self.manager = ConnectionManager()
        self.threshold_listener = get_threshold_listener()

    async def update_device_online_status(self, device_id, is_online):
        """
        Update the isOnline field of a device in Firestore
        """
        try:
            device_ref = db.collection("devices").document(device_id)
            device_ref.update({"isOnline": is_online})
            logger.info(f"Updated online status for device {device_id} to {is_online}")
        except Exception as e:
            logger.error(f"Error updating device online status: {str(e)}")

    async def handle_connection(self, websocket: WebSocket, device_id: str):
        try:
            await self.manager.connect(websocket, device_id)
            logger.info(f"Device connected with ID: {device_id}")

            # Test device connection first
            connection_test = await test_device_connection(device_id)
            if not connection_test:
                logger.error(f"Device connection test failed for {device_id}")

            thresholds = await get_device_thresholds(device_id)
            if not thresholds:
                await self.manager.send_message(
                    device_id,
                    {
                        "type": "error",
                        "message": "Failed to retrieve device thresholds",
                    },
                )
                await websocket.close()
                return

            device_state = DeviceState(device_id, thresholds)
            self.devices[device_id] = device_state

            # Thiết lập threshold listener cho device này
            def threshold_callback(new_thresholds):
                if device_id in self.devices:
                    self.devices[device_id].update_thresholds_from_snapshot(
                        new_thresholds
                    )

            self.threshold_listener.add_device_listener(device_id, threshold_callback)
            logger.info(f"🔥 Threshold listener activated for device {device_id}")

            while True:
                try:
                    data = await websocket.receive_json()
                    image_base64 = data.get("image_base64")
                    timestamp = data.get("timestamp")
                    logger.info(f"timestamp: {timestamp}")

                    if not image_base64 or not timestamp:
                        await self.manager.send_message(
                            device_id,
                            {
                                "type": "error",
                                "message": "Missing image_base64 or timestamp",
                            },
                        )
                        continue

                    analysis_result = await analyze_service.analyze_image_base64(
                        image_base64
                    )
                    logger.info(
                        f"Image analysis result: {analysis_result.get('success')}"
                    )
                    if analysis_result.get("success") is False:
                        logger.error(
                            f"Image analysis failed: {analysis_result.get('message')}"
                        )
                        await self.manager.send_message(
                            device_id,
                            {
                                "type": "error",
                                "message": "Image analysis failed",
                                "details": analysis_result.get("message"),
                            },
                        )
                        continue

                    posture = analysis_result.get("analysis", {}).get("position")
                    logger.info(f"Posture detected: {posture}")
                    if not posture:
                        logger.warning("No posture detected in the image.")
                        await self.manager.send_message(
                            device_id,
                            {
                                "type": "error",
                                "message": "No posture detected in the image",
                            },
                        )
                        continue

                    posture_map = {
                        "Nằm ngửa": "back",
                        "Nằm sấp": "prone",
                        "Nằm nghiêng": "side",
                    }
                    posture = posture_map.get(posture, "unknown")
                    if posture == "unknown":
                        logger.warning("Unknown posture detected.")
                        await self.manager.send_message(
                            device_id,
                            {"type": "error", "message": "Unknown posture detected"},
                        )
                        continue

                    blanket_data = analysis_result.get("analysis").get(
                        "is_covered", True
                    )
                    logger.info(f"Blanket data: {blanket_data}")
                    if not isinstance(blanket_data, bool):
                        logger.warning("Error: 'blanket' data is not a boolean")
                        has_blanket = True
                    else:
                        has_blanket = blanket_data

                    logger.info(f"Blanket status: {has_blanket}")

                    await self.manager.send_message(
                        device_id,
                        {
                            "type": "analysis",
                            "timestamp": timestamp,
                            "posture": posture,
                            "has_blanket": has_blanket,
                        },
                    )

                    device_state.posture_history.append(
                        {
                            "posture": posture,
                            "has_blanket": has_blanket,
                            "timestamp": timestamp,
                        }
                    )

                    if len(device_state.posture_history) > device_state.max_history:
                        device_state.posture_history.pop(0)

                    if len(device_state.posture_history) < device_state.max_history:
                        await device_state.update_position_baby(posture, timestamp)
                    else:
                        side_count = sum(
                            1
                            for p in device_state.posture_history
                            if p["posture"] == posture
                        )
                        if side_count >= 3:
                            await device_state.update_position_baby(posture, timestamp)

                    if len(device_state.posture_history) < device_state.max_history:
                        await device_state.update_blanket_baby(has_blanket, timestamp)
                    else:
                        blanket_count = sum(
                            1
                            for p in device_state.posture_history
                            if p["has_blanket"] == has_blanket
                        )
                        if blanket_count >= 3:
                            await device_state.update_blanket_baby(
                                has_blanket, timestamp
                            )

                    check_position = device_state.check_position_baby()
                    if check_position:
                        # Threshold đã được cập nhật tự động qua listener, không cần đọc lại
                        logger.info(
                            f"Position alert detected for device {device_id} - using real-time thresholds"
                        )
                        logger.info(
                            f"Current thresholds: side={device_state.side_threshold}, prone={device_state.prone_threshold}, no_blanket={device_state.no_blanket_threshold}"
                        )

                        # Kiểm tra với threshold hiện tại
                        if check_position:
                            now_position = device_state.position_baby["position"]

                            threshold = 0
                            if now_position == "side":
                                threshold = device_state.side_threshold
                            elif now_position == "prone":
                                threshold = device_state.prone_threshold

                            logger.info(
                                f"Using updated {now_position} threshold for device {device_id}: {threshold}"
                            )

                            if threshold == 0:
                                logger.info(
                                    f"Position notification skipped for {now_position} - threshold is 0"
                                )
                            elif (
                                device_state.last_notification_time[now_position]
                                is None
                                or device_state.calc_time(
                                    device_state.last_notification_time[now_position],
                                    timestamp,
                                )
                                > 20
                            ):
                                device_state.last_notification_time[now_position] = (
                                    timestamp
                                )
                                image_url = await upload_to_cloudinary(image_base64)

                                await send_notifications(
                                    device_id,
                                    now_position,
                                    # device_state.position_baby["count"],
                                    device_state.calc_time(
                                        device_state.position_baby["first_time"],
                                        device_state.position_baby["last_time"],
                                    ),
                                    timestamp,
                                    image_url,
                                )
                                logger.info(
                                    f"Notification sent for {now_position} position."
                                )
                                await self.manager.send_message(
                                    device_id,
                                    {
                                        "type": "alert",
                                        "timestamp": timestamp,
                                        "message": f"Position alert: {now_position}",
                                        "position": now_position,
                                        "image_url": image_url,
                                    },
                                )

                    check_blanket = device_state.check_blanket_baby()
                    if check_blanket:
                        # Threshold đã được cập nhật tự động qua listener
                        logger.info(
                            f"Blanket alert detected for device {device_id} - using real-time thresholds"
                        )
                        logger.info(
                            f"Current thresholds: side={device_state.side_threshold}, prone={device_state.prone_threshold}, no_blanket={device_state.no_blanket_threshold}"
                        )

                        # Kiểm tra với threshold hiện tại
                        if check_blanket:
                            no_blanket_threshold = device_state.no_blanket_threshold

                            logger.info(
                                f"Using updated no blanket threshold for device {device_id}: {no_blanket_threshold}"
                            )

                            if no_blanket_threshold == 0:
                                logger.info(
                                    "No blanket notification skipped - threshold is 0"
                                )
                            elif (
                                device_state.last_notification_time["noBlanket"] is None
                                or device_state.calc_time(
                                    device_state.last_notification_time["noBlanket"],
                                    timestamp,
                                )
                                > 20
                            ):
                                device_state.last_notification_time["noBlanket"] = (
                                    timestamp
                                )
                                image_url = await upload_to_cloudinary(image_base64)
                                await send_notifications(
                                    device_id,
                                    "noblanket",
                                    # device_state.blanket_baby["count"],
                                    device_state.calc_time(
                                        device_state.blanket_baby["first_time"],
                                        device_state.blanket_baby["last_time"],
                                    ),
                                    timestamp,
                                    image_url,
                                )
                                logger.info("Notification sent for no blanket.")
                                await self.manager.send_message(
                                    device_id,
                                    {
                                        "type": "alert",
                                        "timestamp": timestamp,
                                        "message": "No blanket detected",
                                        "image_url": image_url,
                                    },
                                )

                except WebSocketDisconnect:
                    logger.info(f"Device {device_id} disconnected")
                    break
                except Exception as e:
                    logger.error(f"Error processing data: {str(e)}")
                    await self.manager.send_message(
                        device_id,
                        {
                            "type": "error",
                            "message": "Error processing data",
                            "details": str(e),
                        },
                    )
                    continue

        except WebSocketDisconnect:
            logger.info(f"Device {device_id} disconnected during handshake")
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            await self.manager.send_message(
                device_id,
                {
                    "type": "error",
                    "message": "WebSocket connection error",
                    "details": str(e),
                },
            )
        finally:
            try:
                # await self.update_device_online_status(device_id, False)

                # Remove threshold listener
                self.threshold_listener.remove_device_listener(device_id)
                logger.info(f"🔥 Threshold listener removed for device {device_id}")

                # Remove device from the active devices list
                if device_id in self.devices:
                    del self.devices[device_id]
                    logger.info(
                        f"Device {device_id} disconnected and removed from active devices"
                    )

                # Disconnect the WebSocket
                self.manager.disconnect(device_id)

                logger.info(f"Cleanup completed for device {device_id}")
            except Exception as cleanup_error:
                logger.error(
                    f"Error during cleanup for device {device_id}: {cleanup_error}"
                )
