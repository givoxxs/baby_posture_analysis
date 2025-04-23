import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import cloudinary
import cloudinary.uploader

# Load environment variables
load_dotenv()

# Initialize Firebase using the JSON credential file
cred = credentials.Certificate('babycare_connecction.json')

firebase_admin.initialize_app(cred)
db = firestore.client()

# Initialize Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)
