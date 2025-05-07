from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from app.services.analysis_service import get_singleton_analysis_service
from app.services.device_state import DeviceState
from app.services.notification_service import (
    get_device_thresholds,
    upload_to_cloudinary,
    send_notifications,
)
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

    async def handle_connection(self, websocket: WebSocket, device_id: str):
        try:
            await self.manager.connect(websocket, device_id)
            logger.info(f"Device connected with ID: {device_id}")

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

                    if "is_covered" not in analysis_result:
                        logger.warning(
                            "Error: 'is_covered' key is missing in analysis_result"
                        )
                        has_blanket = False
                    else:
                        blanket_data = analysis_result.get("analysis").get(
                            "is_covered", False
                        )
                        logger.info(f"Blanket data: {blanket_data}")
                        if not isinstance(blanket_data, bool):
                            logger.warning("Error: 'blanket' data is not a boolean")
                            has_blanket = False
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
                        now_position = device_state.position_baby["position"]
                        if (
                            device_state.last_notification_time[now_position] is None
                            or device_state.calc_time(
                                device_state.last_notification_time[now_position],
                                timestamp,
                            )
                            > 10
                        ):
                            device_state.last_notification_time[now_position] = (
                                timestamp
                            )
                            image_url = await upload_to_cloudinary(image_base64)
                            await send_notifications(
                                device_id,
                                now_position,
                                device_state.position_baby["count"],
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
                        if (
                            device_state.last_notification_time["noBlanket"] is None
                            or device_state.calc_time(
                                device_state.last_notification_time["noBlanket"],
                                timestamp,
                            )
                            > 10
                        ):
                            device_state.last_notification_time["noBlanket"] = timestamp
                            image_url = await upload_to_cloudinary(image_base64)
                            await send_notifications(
                                device_id,
                                "no_blanket",
                                device_state.blanket_baby["count"],
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
                if device_id in self.devices:
                    del self.devices[device_id]
                    logger.info(
                        f"Device {device_id} disconnected and removed from active devices"
                    )
                self.manager.disconnect(device_id)
            except Exception as cleanup_error:
                logger.error(
                    f"Error during cleanup for device {device_id}: {cleanup_error}"
                )
