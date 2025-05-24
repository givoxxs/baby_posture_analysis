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


# Đường dẫn file credential
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
credential_file_path = os.path.join(project_root, "babycare_connection.json")

# Kiểm tra và xử lý file credential
if os.path.isfile(credential_file_path):
    # File tồn tại và là file hợp lệ
    logger.info("Sử dụng file babycare_connection.json đã tồn tại")
elif os.path.isdir(credential_file_path):
    # Đường dẫn là thư mục - xóa và tạo lại file từ biến môi trường
    logger.warning(
        f"Đường dẫn {credential_file_path} là thư mục, sẽ xóa và tạo lại file"
    )
    shutil.rmtree(credential_file_path)
    base64_str = os.environ["FIREBASE_CREDENTIAL_BASE64"]
    json_bytes = base64.b64decode(base64_str)
    with open(credential_file_path, "wb") as f:
        f.write(json_bytes)
    logger.info("Đã tạo lại file babycare_connection.json từ environment variable")
else:
    # File không tồn tại - tạo từ biến môi trường
    base64_str = os.environ["FIREBASE_CREDENTIAL_BASE64"]
    json_bytes = base64.b64decode(base64_str)
    with open(credential_file_path, "wb") as f:
        f.write(json_bytes)
    logger.info("Đã tạo file babycare_connection.json từ environment variable")

# Initialize Firebase using the JSON credential file
cred = credentials.Certificate(credential_file_path)
firebase_admin.initialize_app(cred)

# Create credentials object for AsyncClient
credentials = service_account.Credentials.from_service_account_file(
    credential_file_path
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
