from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from app.services.websocket_service import WebSocketHandler
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

websocket_handler = WebSocketHandler()


@router.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    """
    WebSocket endpoint for real-time baby posture analysis.

    Parameters:
    ----------
    websocket : WebSocket
        The WebSocket connection object
    device_id : str
        Unique identifier for the device, used for Firebase and state tracking

    Expected Message Format:
    ---------------------
    JSON object containing:
    {
        "timestamp": float (required)
            Unix timestamp in seconds
        "image_base64": str (required)
            Base64-encoded image data
    }

    Sent Message Types:
    -----------------
    1. Analysis Result:
    {
        "type": "analysis",
        "timestamp": float,
        "posture": str,
        "has_blanket": bool
    }

    2. Alert (on posture or blanket issues):
    {
        "type": "alert",
        "timestamp": float,
        "message": str,
        "position": str (optional),
        "image_url": str
    }

    3. Error:
    {
        "type": "error",
        "message": str,
        "details": str (optional)
    }

    Notes:
    -----
    - Connection remains open for continuous real-time image processing
    - Images are analyzed for baby posture and blanket status
    - Notifications are triggered based on posture history and blanket status
    - Firebase is used for device thresholds and notification events

    Error Handling:
    -------------
    - Missing fields: Sends error message, continues processing
    - Analysis errors: Sends error message, continues processing
    - Connection errors: Logs error, closes connection
    """
    logger.info(f"New WebSocket connection request from device {device_id}")

    try:
        await websocket_handler.handle_connection(websocket, device_id)
    except WebSocketDisconnect:
        logger.info(f"Device {device_id} disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket endpoint for device {device_id}: {str(e)}")
