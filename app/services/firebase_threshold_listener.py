import logging
import asyncio
from typing import Dict, Callable, Optional
from google.cloud import firestore
from app.config import sync_db
import threading

logger = logging.getLogger(__name__)


class FirebaseThresholdListener:
    """
    Service để lắng nghe sự thay đổi threshold từ Firebase Real-time
    """

    def __init__(self):
        self.listeners: Dict[str, firestore.Watch] = {}
        self.threshold_callbacks: Dict[str, Callable] = {}
        self.current_thresholds: Dict[str, Dict] = {}

    def add_device_listener(self, device_id: str, callback: Callable[[Dict], None]):
        """
        Thêm listener cho một device để lắng nghe thay đổi threshold

        Args:
            device_id: ID của device
            callback: Function được gọi khi threshold thay đổi
        """
        if device_id in self.listeners:
            logger.info(f"Device {device_id} already has an active listener")
            return

        def on_snapshot(doc_snapshot, changes, read_time):
            """Callback khi có thay đổi trong Firestore"""
            try:
                for doc in doc_snapshot:
                    if doc.exists:
                        device_data = doc.to_dict()
                        new_thresholds = {
                            "sideThreshold": device_data.get("sideThreshold", 10),
                            "proneThreshold": device_data.get("proneThreshold", 10),
                            "noBlanketThreshold": device_data.get(
                                "noBlanketThreshold", 100
                            ),
                        }

                        # Kiểm tra nếu threshold thực sự thay đổi
                        old_thresholds = self.current_thresholds.get(device_id, {})
                        if new_thresholds != old_thresholds:
                            logger.info(f"🔥 THRESHOLD CHANGED for device {device_id}")
                            logger.info(f"Old thresholds: {old_thresholds}")
                            logger.info(f"New thresholds: {new_thresholds}")

                            self.current_thresholds[device_id] = new_thresholds

                            # Gọi callback để cập nhật
                            if device_id in self.threshold_callbacks:
                                self.threshold_callbacks[device_id](new_thresholds)
                    else:
                        logger.warning(f"Device {device_id} document does not exist")
            except Exception as e:
                logger.error(f"Error in threshold listener callback: {e}")

        try:
            # Tạo listener cho document device
            doc_ref = sync_db.collection("devices").document(device_id)
            listener = doc_ref.on_snapshot(on_snapshot)

            self.listeners[device_id] = listener
            self.threshold_callbacks[device_id] = callback

            logger.info(f"✅ Started threshold listener for device {device_id}")

            # Lấy threshold hiện tại
            doc = doc_ref.get()
            if doc.exists:
                device_data = doc.to_dict()
                initial_thresholds = {
                    "sideThreshold": device_data.get("sideThreshold", 10),
                    "proneThreshold": device_data.get("proneThreshold", 10),
                    "noBlanketThreshold": device_data.get("noBlanketThreshold", 100),
                }
                self.current_thresholds[device_id] = initial_thresholds
                logger.info(
                    f"Initial thresholds for device {device_id}: {initial_thresholds}"
                )

        except Exception as e:
            logger.error(
                f"Error starting threshold listener for device {device_id}: {e}"
            )

    def remove_device_listener(self, device_id: str):
        """
        Loại bỏ listener cho một device
        """
        if device_id in self.listeners:
            try:
                self.listeners[device_id].unsubscribe()
                del self.listeners[device_id]
                if device_id in self.threshold_callbacks:
                    del self.threshold_callbacks[device_id]
                if device_id in self.current_thresholds:
                    del self.current_thresholds[device_id]
                logger.info(f"❌ Removed threshold listener for device {device_id}")
            except Exception as e:
                logger.error(
                    f"Error removing threshold listener for device {device_id}: {e}"
                )

    def get_current_thresholds(self, device_id: str) -> Optional[Dict]:
        """
        Lấy threshold hiện tại của device từ cache
        """
        return self.current_thresholds.get(device_id)

    def stop_all_listeners(self):
        """
        Dừng tất cả listeners
        """
        for device_id in list(self.listeners.keys()):
            self.remove_device_listener(device_id)
        logger.info("Stopped all threshold listeners")


# Singleton instance
_threshold_listener_instance = None


def get_threshold_listener() -> FirebaseThresholdListener:
    """
    Lấy singleton instance của FirebaseThresholdListener
    """
    global _threshold_listener_instance
    if _threshold_listener_instance is None:
        _threshold_listener_instance = FirebaseThresholdListener()
    return _threshold_listener_instance
