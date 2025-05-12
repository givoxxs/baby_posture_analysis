from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect  # type: ignore
from fastapi.responses import JSONResponse  # type: ignore
from typing import Optional, Dict, Any, List
import traceback
import logging
from datetime import datetime, timedelta
import asyncio
import cv2
import numpy as np
import io
import json
import time
import base64
from pathlib import Path
import tempfile
import os
import uuid

from app.services.analysis_service import (
    AnalysisService,
    get_singleton_analysis_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analyze", tags=["analyze_video"])


class SafetyMonitor:
    """
    Monitor the safety conditions of a baby from video analysis results
    """

    def __init__(self):
        # self.face_covered_count = 0
        self.prone_position_count = 0  # Nằm sấp count
        self.side_position_count = 0  # Nằm nghiêng count
        self.no_blanket_count = 0
        self.total_frames = 0
        self.frame_history = []

        # Constants for safety thresholds (in seconds/frames)
        # self.FACE_COVERED_THRESHOLD = 10   # Face covered for 10s is dangerous
        self.PRONE_THRESHOLD = 20  # Lying on stomach for 20s is dangerous
        self.SIDE_THRESHOLD = 30  # Lying on side for 30s is warning
        self.NO_BLANKET_THRESHOLD = 60  # No blanket for 60s is warning

    def update(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the safety monitor with a new frame analysis

        Args:
            analysis_result: The analysis result from a single frame

        Returns:
            Dict with safety warnings/alerts
        """
        if not analysis_result.get("success", False):
            return {}

        self.total_frames += 1

        # Keep only the most recent 120 frames in history (2 minutes)
        if len(self.frame_history) >= 120:
            self.frame_history.pop(0)

        # Add current frame to history
        self.frame_history.append(
            {
                "timestamp": analysis_result.get("timestamp"),
                "position": analysis_result.get("analysis", {}).get("position_id"),
                # "face_covered": analysis_result.get("analysis", {}).get("face_covered", False),
                "is_covered": analysis_result.get("analysis", {}).get(
                    "is_covered", True
                ),  # Default to covered
            }
        )

        # Calculate consecutive counts for different conditions
        # face_covered_streak = self._calculate_consecutive_condition(lambda frame: frame["face_covered"])
        prone_position_streak = self._calculate_consecutive_condition(
            lambda frame: frame["position"] == 2
        )  # 2 = Nằm sấp
        side_position_streak = self._calculate_consecutive_condition(
            lambda frame: frame["position"] == 1
        )  # 1 = Nằm nghiêng
        no_blanket_streak = self._calculate_consecutive_condition(
            lambda frame: not frame["is_covered"]
        )

        # Create safety warnings based on current conditions
        safety_warnings = {}

        # if face_covered_streak >= self.FACE_COVERED_THRESHOLD:
        #     safety_warnings["face_covered"] = {
        #         "level": "danger",
        #         "message": f"NGUY HIỂM: Mặt bé bị che khuất liên tục {face_covered_streak} giây!",
        #         "streak": face_covered_streak
        #     }

        if prone_position_streak >= self.PRONE_THRESHOLD:
            safety_warnings["prone_position"] = {
                "level": "danger",
                "message": f"NGUY HIỂM: Bé nằm sấp liên tục {prone_position_streak} giây!",
                "streak": prone_position_streak,
            }

        if side_position_streak >= self.SIDE_THRESHOLD:
            safety_warnings["side_position"] = {
                "level": "warning",
                "message": f"CẢNH BÁO: Bé nằm nghiêng liên tục {side_position_streak} giây!",
                "streak": side_position_streak,
            }

        if no_blanket_streak >= self.NO_BLANKET_THRESHOLD:
            safety_warnings["no_blanket"] = {
                "level": "warning",
                "message": f"CẢNH BÁO: Bé không đắp chăn liên tục {no_blanket_streak} giây!",
                "streak": no_blanket_streak,
            }

        return safety_warnings

    def _calculate_consecutive_condition(self, condition_fn) -> int:
        """Calculate the number of consecutive frames where a condition is true"""
        if not self.frame_history:
            return 0

        count = 0
        # Count from most recent frame backward
        for frame in reversed(self.frame_history):
            if condition_fn(frame):
                count += 1
            else:
                break

        return count

    def get_stats(self) -> Dict[str, Any]:
        """Get overall statistics from the monitoring session"""
        if not self.frame_history:
            return {
                "total_frames": 0,
                "duration_seconds": 0,
                "positions": {"back": 0, "side": 0, "stomach": 0},
                # "face_covered_percentage": 0,
                "blanket_percentage": 0,
            }

        positions = {0: 0, 1: 0, 2: 0}  # 0: back, 1: side, 2: stomach
        face_covered_count = 0
        blanket_count = 0

        for frame in self.frame_history:
            if frame["position"] in positions:
                positions[frame["position"]] += 1
            # if frame["face_covered"]:
            #     face_covered_count += 1
            if frame["is_covered"]:
                blanket_count += 1

        total = len(self.frame_history)

        return {
            "total_frames": total,
            "duration_seconds": total,
            "positions": {
                "back": positions.get(0, 0) / total if total else 0,
                "side": positions.get(1, 0) / total if total else 0,
                "stomach": positions.get(2, 0) / total if total else 0,
            },
            "face_covered_percentage": face_covered_count / total if total else 0,
            "blanket_percentage": blanket_count / total if total else 0,
        }


class VideoAnalyzer:
    """Helper class for analyzing video streams"""

    def __init__(self, analysis_service: AnalysisService):
        self.analysis_service = analysis_service
        self.safety_monitor = SafetyMonitor()
        self.frame_rate = 1  # Process 1 frame per second

    async def process_video_file(self, file_path: str) -> Dict[str, Any]:
        """Process a complete video file and return comprehensive results"""
        try:
            capture = cv2.VideoCapture(file_path)
            if not capture.isOpened():
                return {"success": False, "message": "Không thể mở file video"}

            frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = capture.get(cv2.CAP_PROP_FPS)
            duration = frame_count / fps if fps > 0 else 0

            # Process at most one frame per second
            frames_to_process = min(frame_count, int(duration))
            frames_interval = max(1, int(fps))  # Skip frames to achieve ~1fps

            results = []
            timestamps = []
            safety_alerts = []

            # Process frames
            frame_index = 0
            while capture.isOpened() and frame_index < frame_count:
                capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
                success, frame = capture.read()
                if not success:
                    break

                # Calculate timestamp
                timestamp = datetime.now().replace(microsecond=0).isoformat()
                if fps > 0:
                    seconds = frame_index / fps
                    timestamps.append(seconds)
                    timestamp = (
                        datetime.now() + timedelta(seconds=seconds)
                    ).isoformat()

                # Analyze this frame
                result = await self._process_frame(frame, timestamp)

                if result.get("success", False):
                    # Check safety conditions
                    safety_result = self.safety_monitor.update(result)
                    if safety_result:
                        result["safety_alerts"] = safety_result
                        safety_alerts.append(
                            {
                                "timestamp": timestamp,
                                "frame_index": frame_index,
                                "alerts": safety_result,
                            }
                        )

                    results.append(
                        {
                            "timestamp": timestamp,
                            "frame_index": frame_index,
                            "analysis": result.get("analysis", {}),
                            "safety_alerts": safety_result,
                        }
                    )

                # Move to next frame to process
                frame_index += frames_interval

            capture.release()

            # Generate summary statistics
            stats = self.safety_monitor.get_stats()

            return {
                "success": True,
                "video_info": {
                    "frame_count": frame_count,
                    "fps": fps,
                    "duration_seconds": duration,
                    "processed_frames": len(results),
                },
                "statistics": stats,
                "frames": results,
                "safety_alerts": safety_alerts,
                "has_alerts": len(safety_alerts) > 0,
            }

        except Exception as e:
            logger.error(f"Error processing video: {str(e)}\n{traceback.format_exc()}")
            return {"success": False, "message": f"Error processing video: {str(e)}"}

    async def _process_frame(self, frame, timestamp) -> Dict[str, Any]:
        """Process a single video frame"""
        try:
            # Analyze the frame using our pipeline
            result = self.analysis_service.pipeline.analyze_image(frame, timestamp)
            return result
        except Exception as e:
            logger.error(f"Error processing frame: {str(e)}")
            return {"success": False, "message": f"Error processing frame: {str(e)}"}


@router.post("/video")
async def analyze_baby_video(
    file: UploadFile = File(...),
    analysis_service: AnalysisService = Depends(get_singleton_analysis_service),
):
    """
    Analyze a video of a baby to detect posture, face covering, and blanket covering over time

    This endpoint processes a video file by:
    1. Extracting frames at 1 frame per second
    2. Analyzing each frame for baby posture, face covering, and blanket covering
    3. Monitoring for dangerous conditions (face covered for 10+ seconds, prone position for 20+ seconds)
    4. Providing warnings (side position for 30+ seconds, no blanket for 60+ seconds)

    Parameters:
    - file: Video file to analyze (.mp4, .avi, etc.)

    Returns:
    - Comprehensive analysis including all frames, safety alerts, and overall statistics
    """
    try:
        # Create a temporary file to store the uploaded video
        suffix = Path(file.filename).suffix if file.filename else ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            # Write uploaded file to temp file
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Process the video
            analyzer = VideoAnalyzer(analysis_service)
            result = await analyzer.process_video_file(temp_file_path)

            if not result.get("success", False):
                return JSONResponse(status_code=422, content=result)

            # Return results
            return JSONResponse(content=result)

        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in baby video analysis: {str(e)}\n{error_details}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Error in baby video analysis: {str(e)}",
            },
        )


@router.websocket("/video-stream")
async def analyze_video_stream(
    websocket: WebSocket,
    analysis_service: AnalysisService = Depends(get_singleton_analysis_service),
):
    """
    WebSocket endpoint to analyze a live video stream

    Client should send video frames as base64-encoded images with optional timestamps.
    Server will respond with analysis results for each frame.
    """
    await websocket.accept()

    analyzer = VideoAnalyzer(analysis_service)
    safety_monitor = SafetyMonitor()

    try:
        while True:
            # Receive frame data from client
            data = await websocket.receive_text()
            try:
                frame_data = json.loads(data)

                # Extract image data and timestamp
                image_base64 = frame_data.get("image")
                timestamp = frame_data.get("timestamp", datetime.now().isoformat())

                if not image_base64:
                    await websocket.send_json(
                        {"success": False, "message": "No image data received"}
                    )
                    continue

                # Decode base64 image
                image_bytes = base64.b64decode(
                    image_base64.split(",")[1] if "," in image_base64 else image_base64
                )
                nparr = np.frombuffer(image_bytes, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if frame is None:
                    await websocket.send_json(
                        {"success": False, "message": "Failed to decode image"}
                    )
                    continue

                # Process the frame
                result = await analyzer._process_frame(frame, timestamp)

                # Update safety monitor
                if result.get("success", False):
                    safety_results = safety_monitor.update(result)
                    result["safety_alerts"] = safety_results

                # Send results back to client
                await websocket.send_json(result)

            except json.JSONDecodeError:
                await websocket.send_json(
                    {"success": False, "message": "Invalid JSON data"}
                )

            except Exception as e:
                logger.error(f"Error processing stream frame: {str(e)}")
                await websocket.send_json(
                    {"success": False, "message": f"Error processing frame: {str(e)}"}
                )

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.close()
        except:
            pass
