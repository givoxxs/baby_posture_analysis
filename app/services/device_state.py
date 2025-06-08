from datetime import datetime
from app.services.notification_service import send_event_to_firestore
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)


class DeviceState:
    def __init__(self, device_id, thresholds):
        self.device_id = device_id
        self.side_threshold = thresholds.get(
            "sideThreshold", int(os.getenv("SIDE_THRESHOLD", 30))
        )
        self.prone_threshold = thresholds.get(
            "proneThreshold", int(os.getenv("PRONE_THRESHOLD", 40))
        )
        self.no_blanket_threshold = thresholds.get(
            "noBlanketThreshold", int(os.getenv("NO_BLANKET_THRESHOLD", 100))
        )
        self.max_history = int(os.getenv("MAX_HISTORY", 5))
        self.position_baby = {
            "position": "",
            "count": 0,
            "first_time": None,
            "last_time": None,
        }
        self.blanket_baby = {
            "is_covered": True,
            "count": 0,
            "first_time": None,
            "last_time": None,
        }
        self.posture_history = []

        self.last_notification_time = {"noBlanket": None, "side": None, "prone": None}

    def update_thresholds_from_snapshot(self, new_thresholds):
        """
        Cập nhật threshold từ Firebase snapshot listener
        """
        old_side = self.side_threshold
        old_prone = self.prone_threshold
        old_blanket = self.no_blanket_threshold

        self.side_threshold = new_thresholds.get("sideThreshold", self.side_threshold)
        self.prone_threshold = new_thresholds.get(
            "proneThreshold", self.prone_threshold
        )
        self.no_blanket_threshold = new_thresholds.get(
            "noBlanketThreshold", self.no_blanket_threshold
        )

        logger.info(f"🔄 Threshold updated for device {self.device_id}:")
        logger.info(f"   Side: {old_side} → {self.side_threshold}")
        logger.info(f"   Prone: {old_prone} → {self.prone_threshold}")
        logger.info(f"   No Blanket: {old_blanket} → {self.no_blanket_threshold}")

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
            self.blanket_baby["first_time"] = timestamp
            self.blanket_baby["last_time"] = timestamp
            if is_covered == False:
                await send_event_to_firestore(self.device_id, "noblanket", timestamp)
            else:
                await send_event_to_firestore(self.device_id, "blanket", timestamp)

    # Calculate seconds between two timestamps
    def calc_time(self, start_time, end_time):
        if start_time is None or end_time is None:
            return 0
        start_time = datetime.fromisoformat(start_time)
        end_time = datetime.fromisoformat(end_time)
        res = (end_time - start_time).total_seconds()
        # Convert to integer
        return int(res)

    def check_position_baby(self):
        if self.position_baby["position"] == "side":
            if (
                self.position_baby["count"] >= self.side_threshold * 80 / 100
                and self.position_baby["last_time"] is not None
                and self.calc_time(
                    self.position_baby["first_time"], self.position_baby["last_time"]
                )
                >= (self.side_threshold)
            ):
                return True
            else:
                return False
        elif self.position_baby["position"] == "prone":
            if (
                self.position_baby["count"] >= self.prone_threshold * 80 / 100
                and self.position_baby["last_time"] is not None
                and self.calc_time(
                    self.position_baby["first_time"], self.position_baby["last_time"]
                )
                >= (self.prone_threshold)
            ):
                return True
            else:
                return False
        return False

    def check_blanket_baby(self):
        if self.no_blanket_threshold == 0:
            return False
        if self.blanket_baby["is_covered"] == False:
            if (
                self.blanket_baby["count"] >= self.no_blanket_threshold * 80 / 100
                and self.blanket_baby["last_time"] is not None
                and self.calc_time(
                    self.blanket_baby["first_time"], self.blanket_baby["last_time"]
                )
                >= (self.no_blanket_threshold)
            ):
                return True
            else:
                return False
        else:
            return False
