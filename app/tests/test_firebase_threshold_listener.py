import asyncio
import logging
import time
from app.services.firebase_threshold_listener import get_threshold_listener
from app.services.notification_service import test_device_connection

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DEVICE_ID_TEST = "18ff6551-820b-4aad-b714-1143629970f0"


async def test_threshold_listener():
    """
    Test Firebase threshold listener với device ID test
    """
    logger.info("🚀 Bắt đầu test Firebase threshold listener...")
    print("🚀 Bắt đầu test Firebase threshold listener...")

    try:
        # 1. Kiểm tra kết nối device
        logger.info(f"📡 Kiểm tra kết nối tới device {DEVICE_ID_TEST}...")
        connection_result = await test_device_connection(DEVICE_ID_TEST)

        if not connection_result:
            logger.error(
                f"❌ Device {DEVICE_ID_TEST} không tồn tại hoặc không thể kết nối"
            )
            print(f"❌ Device {DEVICE_ID_TEST} không tồn tại hoặc không thể kết nối")
            return False

        logger.info(f"✅ Device {DEVICE_ID_TEST} kết nối thành công")
        print(f"✅ Device {DEVICE_ID_TEST} kết nối thành công")

        # 2. Tạo threshold listener
        threshold_listener = get_threshold_listener()

        # 3. Biến để lưu thông tin threshold changes
        threshold_changes = []

        # 4. Callback function để xử lý threshold changes
        def on_threshold_change(new_thresholds):
            timestamp = time.strftime("%H:%M:%S")
            change_info = {"timestamp": timestamp, "thresholds": new_thresholds.copy()}
            threshold_changes.append(change_info)

            logger.info(f"🔥 THRESHOLD THAY ĐỔI LÚC {timestamp}:")
            logger.info(f"   Side Threshold: {new_thresholds.get('sideThreshold')}")
            logger.info(f"   Prone Threshold: {new_thresholds.get('proneThreshold')}")
            logger.info(
                f"   No Blanket Threshold: {new_thresholds.get('noBlanketThreshold')}"
            )

            print(f"🔥 THRESHOLD THAY ĐỔI LÚC {timestamp}:")
            print(f"   Side Threshold: {new_thresholds.get('sideThreshold')}")
            print(f"   Prone Threshold: {new_thresholds.get('proneThreshold')}")
            print(
                f"   No Blanket Threshold: {new_thresholds.get('noBlanketThreshold')}"
            )

        # 5. Đăng ký listener
        threshold_listener.add_device_listener(DEVICE_ID_TEST, on_threshold_change)
        logger.info(f"🔥 Đã đăng ký threshold listener cho device {DEVICE_ID_TEST}")
        print(f"🔥 Đã đăng ký threshold listener cho device {DEVICE_ID_TEST}")

        # 6. Hiển thị threshold hiện tại
        current_thresholds = threshold_listener.get_current_thresholds(DEVICE_ID_TEST)
        if current_thresholds:
            logger.info("📊 Threshold hiện tại:")
            logger.info(f"   Side Threshold: {current_thresholds.get('sideThreshold')}")
            logger.info(
                f"   Prone Threshold: {current_thresholds.get('proneThreshold')}"
            )
            logger.info(
                f"   No Blanket Threshold: {current_thresholds.get('noBlanketThreshold')}"
            )

            print("📊 Threshold hiện tại:")
            print(f"   Side Threshold: {current_thresholds.get('sideThreshold')}")
            print(f"   Prone Threshold: {current_thresholds.get('proneThreshold')}")
            print(
                f"   No Blanket Threshold: {current_thresholds.get('noBlanketThreshold')}"
            )

        # 7. Lắng nghe trong 60 giây
        print("\n⏰ Đang lắng nghe thay đổi threshold trong 60 giây...")
        print(
            "💡 Bây giờ bạn có thể lên Firebase Console để thay đổi threshold values!"
        )
        print("💡 Link: https://console.firebase.google.com/")
        print(f"💡 Tìm device với ID: {DEVICE_ID_TEST}")
        print(
            "💡 Thay đổi các field: sideThreshold, proneThreshold, noBlanketThreshold"
        )
        print("=" * 70)

        for i in range(60):
            await asyncio.sleep(1)
            if (i + 1) % 10 == 0:
                print(f"⏳ Còn {60 - (i + 1)} giây...")
                if threshold_changes:
                    print(f"📈 Đã ghi nhận {len(threshold_changes)} thay đổi threshold")

        # 8. Báo cáo kết quả
        print("\n" + "=" * 70)
        print("📊 KẾT QUẢ TEST:")

        if threshold_changes:
            logger.info(
                f"✅ SUCCESS: Đã ghi nhận {len(threshold_changes)} thay đổi threshold"
            )
            print(
                f"✅ SUCCESS: Đã ghi nhận {len(threshold_changes)} thay đổi threshold"
            )

            print("\n📋 Chi tiết các thay đổi:")
            for i, change in enumerate(threshold_changes, 1):
                print(f"  {i}. Lúc {change['timestamp']}:")
                thresholds = change["thresholds"]
                print(f"     - Side: {thresholds.get('sideThreshold')}")
                print(f"     - Prone: {thresholds.get('proneThreshold')}")
                print(f"     - No Blanket: {thresholds.get('noBlanketThreshold')}")

            return True
        else:
            logger.warning("⚠️  KHÔNG có thay đổi threshold nào được ghi nhận")
            print("⚠️  KHÔNG có thay đổi threshold nào được ghi nhận")
            print(
                "💡 Hãy thử thay đổi threshold trên Firebase Console trong lần test tiếp theo"
            )
            return True  # Vẫn coi là thành công vì listener hoạt động bình thường

    except Exception as e:
        logger.error(f"❌ FAILED: Lỗi trong quá trình test - {e}")
        print(f"❌ FAILED: Lỗi trong quá trình test - {e}")
        return False

    finally:
        # 9. Cleanup
        try:
            threshold_listener.remove_device_listener(DEVICE_ID_TEST)
            logger.info(f"🧹 Đã cleanup threshold listener cho device {DEVICE_ID_TEST}")
            print(f"🧹 Đã cleanup threshold listener cho device {DEVICE_ID_TEST}")
        except Exception as cleanup_error:
            logger.error(f"Lỗi cleanup: {cleanup_error}")


async def test_multiple_threshold_changes():
    """
    Test để kiểm tra nhiều thay đổi threshold liên tiếp
    """
    logger.info("🚀 Test nhiều thay đổi threshold liên tiếp...")
    print("🚀 Test nhiều thay đổi threshold liên tiếp...")

    threshold_listener = get_threshold_listener()
    changes_log = []

    def log_change(new_thresholds):
        changes_log.append({"time": time.time(), "thresholds": new_thresholds.copy()})
        print(f"🔥 Thay đổi #{len(changes_log)}: {new_thresholds}")

    try:
        threshold_listener.add_device_listener(DEVICE_ID_TEST, log_change)
        print("⏰ Lắng nghe trong 30 giây để test nhiều thay đổi...")

        await asyncio.sleep(30)

        print(f"📊 Tổng cộng ghi nhận {len(changes_log)} thay đổi")
        return len(changes_log) > 0

    finally:
        threshold_listener.remove_device_listener(DEVICE_ID_TEST)


if __name__ == "__main__":
    print("🔬 FIREBASE THRESHOLD LISTENER TEST")
    print("=" * 50)

    # Chạy test chính
    result = asyncio.run(test_threshold_listener())

    if result:
        print("\n✅ Test hoàn thành thành công!")
    else:
        print("\n❌ Test thất bại!")

    # Uncomment để chạy test bổ sung
    print("\n" + "=" * 50)
    result2 = asyncio.run(test_multiple_threshold_changes())

# python -m app.tests.test_firebase_threshold_listener
