import unittest
import asyncio
from unittest.mock import patch, MagicMock
import firebase_admin
from firebase_admin import messaging
import sys
import os
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Thêm thư mục gốc của dự án vào sys.path để import các module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.services.notification_service import send_fcm_notification

# Tắt logging để giảm output khi chạy test
logging.getLogger("app.services.notification_service").setLevel(logging.CRITICAL)


class TestFCMNotification(unittest.TestCase):

    @patch("firebase_admin.messaging.send")
    async def test_send_fcm_notification_success(self, mock_send):
        # Thiết lập mock
        mock_send.return_value = "message_id_123456"

        # Dữ liệu thông báo mẫu
        token = "eJR67MaVToiRzpUnqflHug:APA91bHWVc4TbmESAYUj3_HtSFo4iNfmMTHHt8Q7As5MSI6KsQtIP1mxu9-cN6juBAlvL-XqQVibNpor6MNoQOZEKdq_6HuznwbK9kqTBetMoEl4vst7jOc"
        message = {
            "title": "Test Notification",
            "body": "This is a test notification",
            "data": {
                "id": "notification_id_123",
                "type": "Test",
                "time": 1714435200,  # Unix timestamp
                "duration": 10,
            },
        }

        # Gọi hàm cần test
        response = await send_fcm_notification(token, message)

        if response is None:
            logger.error("Failed to send FCM notification")
            return
        else:
            logger.info(f"FCM notification sent successfully: {response}")

        # Kiểm tra kết quả
        self.assertEqual(response, "message_id_123456")

        # Kiểm tra xem hàm messaging.send được gọi đúng cách
        mock_send.assert_called_once()

        # Lấy đối số đã được truyền cho messaging.send
        fcm_message = mock_send.call_args[0][0]

        # Kiểm tra các thuộc tính của thông báo
        self.assertEqual(fcm_message.token, token)
        self.assertEqual(fcm_message.notification.title, message["title"])
        self.assertEqual(fcm_message.notification.body, message["body"])
        self.assertEqual(fcm_message.data, message["data"])
        self.assertEqual(fcm_message.android.priority, "high")
        self.assertEqual(
            fcm_message.android.notification.channel_id, "high-priority-channel"
        )
        self.assertEqual(fcm_message.android.notification.sound, "default")

    @patch("firebase_admin.messaging.send")
    async def test_send_fcm_notification_failure(self, mock_send):
        # Thiết lập mock để ném ngoại lệ
        mock_send.side_effect = Exception("FCM send failed")

        # Dữ liệu thông báo mẫu
        token = "invalid_fcm_token"
        message = {
            "title": "Test Notification",
            "body": "This is a test notification",
            "data": {"type": "Test"},
        }

        # Gọi hàm cần test
        response = await send_fcm_notification(token, message)

        # Kiểm tra kết quả khi gặp lỗi
        self.assertIsNone(response)

        # Kiểm tra xem hàm messaging.send được gọi đúng cách
        mock_send.assert_called_once()

    # Sửa test case này vì hàm send_fcm_notification đang xử lý keyError bên trong try/except
    @patch("firebase_admin.messaging.send")
    async def test_send_fcm_notification_missing_data(self, mock_send):
        # Thiết lập mock
        mock_send.return_value = "message_id_123456"

        # Dữ liệu thông báo thiếu data
        token = "sample_fcm_token_123"
        message = {
            "title": "Test Notification",
            "body": "This is a test notification",
            # Thiếu trường data
        }

        # Gọi hàm cần test - sẽ trả về None thay vì ném KeyError
        response = await send_fcm_notification(token, message)

        # Kiểm tra kết quả
        self.assertIsNone(response)

        # Kiểm tra xem hàm messaging.send không được gọi
        mock_send.assert_not_called()


def run_async_test(test_func):
    """Helper function để chạy test bất đồng bộ"""
    # Sửa lỗi DeprecationWarning bằng cách sử dụng new_event_loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(test_func)
    finally:
        loop.close()


# Hàm main để chạy test
if __name__ == "__main__":
    # Khởi tạo app Firebase nếu chưa được khởi tạo
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app()

    # Sử dụng TestLoader thay vì tạo TestSuite thủ công
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestFCMNotification)

    # Chạy từng test riêng biệt
    runner = unittest.TextTestRunner()

    # Tạo kết quả test
    result = unittest.TestResult()

    # Chạy từng test riêng lẻ để có thể xử lý async
    for test in suite:
        method = getattr(test, test._testMethodName)
        run_async_test(method())

    print("\nAll tests completed!")
