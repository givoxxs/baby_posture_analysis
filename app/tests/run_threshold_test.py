#!/usr/bin/env python3
"""
Script để chạy test Firebase Threshold Listener
Sử dụng: python run_threshold_test.py
"""

import sys
import os
import asyncio

# Thêm thư mục root vào Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import test function
from app.tests.test_firebase_threshold_listener import test_threshold_listener

if __name__ == "__main__":
    print("🔬 FIREBASE THRESHOLD LISTENER TEST")
    print("=" * 60)
    print("📋 Test này sẽ:")
    print("   1. Kết nối tới Firebase device test")
    print("   2. Thiết lập threshold listener")
    print("   3. Lắng nghe thay đổi threshold trong 60 giây")
    print("   4. Báo cáo kết quả")
    print("=" * 60)
    print("")

    try:
        # Chạy test
        result = asyncio.run(test_threshold_listener())

        if result:
            print("🎉 Test hoàn thành thành công!")
            print("💡 Threshold listener đang hoạt động chính xác")
        else:
            print("❌ Test thất bại!")
            print("💡 Kiểm tra lại cấu hình Firebase và device ID")

    except KeyboardInterrupt:
        print("\n⏹️  Test bị dừng bởi người dùng")
    except Exception as e:
        print(f"\n❌ Lỗi không mong muốn: {e}")
        sys.exit(1)

# python -m app.tests.run_threshold_test
