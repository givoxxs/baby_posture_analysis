import os
import tempfile
import shutil
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import cloudinary
import cloudinary.uploader
from google.cloud.firestore_v1.async_client import AsyncClient
from google.oauth2 import service_account
import base64

import logging

logger = logging.getLogger(__name__)

load_dotenv()
# Đường dẫn tuyệt đối cho file credential
credential_file_path = os.path.join(os.getcwd(), "babycare_connection.json")

# Kiểm tra xem file credential đã tồn tại hay chưa
if not os.path.exists(credential_file_path) or not os.path.isfile(credential_file_path):
    base64_str = os.environ["FIREBASE_CREDENTIAL_BASE64"]
    json_bytes = base64.b64decode(base64_str)

    # Kiểm tra và xóa nếu tồn tại thư mục cùng tên
    if os.path.exists(credential_file_path) and os.path.isdir(credential_file_path):
        shutil.rmtree(credential_file_path)

    # Tạo file credential mới
    with open(credential_file_path, "wb") as f:
        f.write(json_bytes)
    logger.info("Đã tạo file babycare_connection.json từ environment variable")
else:
    logger.info("Sử dụng file babycare_connection.json đã tồn tại")

# Initialize Firebase using the JSON credential file
cred = credentials.Certificate("babycare_connection.json")
firebase_admin.initialize_app(cred)

# Create credentials object for AsyncClient
credentials = service_account.Credentials.from_service_account_file(
    "babycare_connection.json"
)

# Initialize Firestore clients
db = AsyncClient(project=cred.project_id, credentials=credentials)
sync_db = firestore.client()

# Initialize Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)
