import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import cloudinary
import cloudinary.uploader
from google.cloud.firestore_v1.async_client import AsyncClient
from google.oauth2 import service_account

# Load environment variables
load_dotenv()

# Initialize Firebase using the JSON credential file
cred = credentials.Certificate('babycare_connection.json')
firebase_admin.initialize_app(cred)

# Create credentials object for AsyncClient
credentials = service_account.Credentials.from_service_account_file(
    'babycare_connection.json'
)

# Initialize Firestore clients
db = AsyncClient(
    project=cred.project_id,
    credentials=credentials
)
sync_db = firestore.client()

# Initialize Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)