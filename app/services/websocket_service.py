import json
import asyncio
import base64
import time
from datetime import datetime
import cloudinary.uploader
from app.config import db
from app.services.analysis_service import get_singleton_analysis_service

analyze_image = get_singleton_analysis_service()

class DeviceState:
    def __init__(self, device_id, thresholds):
        self.device_id = device_id
        self.side_threshold = thresholds.get('sideThreshold', 50)
        self.prone_threshold = thresholds.get('proneThreshold', 50)
        self.no_blanket_threshold = thresholds.get('noBlanketThreshold', 50)
        self.posture_history = []
        self.last_notification_time = {
            'side': 0,
            'prone': 0,
            'noBlanket': 0
        }
        self.continuous_state = {
            'side': 0,
            'prone': 0,
            'noBlanket': 0
        }
        self.start_time = {
            'side': None,
            'prone': None,
            'noBlanket': None
        }

async def get_device_thresholds(device_id):
    device_doc = await db.collection('Device').where('deviceId', '==', device_id).get()
    if not device_doc or len(device_doc) == 0:
        return None
    return device_doc[0].to_dict()

async def upload_to_cloudinary(image_base64):
    try:
        result = cloudinary.uploader.upload(f"data:image/jpeg;base64,{image_base64}")
        return result['secure_url']
    except Exception as e:
        print(f"Error uploading to Cloudinary: {e}")
        return None

async def send_notifications(device_id, event_type, duration, start_time, image_url=None):
    # Send to PushNotification collection
    push_notification = {
        'deviceId': device_id,
        'type': event_type,
        'duration': duration,
        'time': start_time
    }
    await db.collection('PushNotification').add(push_notification)

    # Send to Notification collection with image
    if image_url:
        notification = {
            'deviceId': device_id,
            'type': event_type,
            'duration': duration,
            'time': start_time,
            'imageUrl': image_url
        }
        await db.collection('Notification').add(notification)

class WebSocketHandler:
    def __init__(self):
        self.devices = {}

    async def handle_connection(self, websocket):
        try:
            # First message should be device ID
            device_id = await websocket.recv()
            print(f"Device connected with ID: {device_id}")

            # Get device thresholds from Firebase
            thresholds = await get_device_thresholds(device_id)
            if not thresholds:
                await websocket.close()
                return

            # Initialize device state
            device_state = DeviceState(device_id, thresholds)
            self.devices[device_id] = device_state

            while True:
                message = await websocket.recv()
                data = json.loads(message)
                
                # Extract image and timestamp
                image_base64 = data.get('image_base64')
                timestamp = data.get('timestamp')

                if not image_base64 or not timestamp:
                    continue

                # Analyze image
                analysis_result = await analyze_image(image_base64)
                posture = analysis_result.get('posture')
                has_blanket = analysis_result.get('has_blanket', True)

                current_time = time.time()
                
                # Update posture history
                device_state.posture_history.append({
                    'posture': posture,
                    'has_blanket': has_blanket,
                    'timestamp': current_time
                })

                # Keep only last minute of history
                device_state.posture_history = [
                    entry for entry in device_state.posture_history 
                    if current_time - entry['timestamp'] <= 60
                ]

                # Check for side position
                if posture == 'side':
                    if device_state.start_time['side'] is None:
                        device_state.start_time['side'] = current_time
                    device_state.continuous_state['side'] = current_time - device_state.start_time['side']
                    
                    if (device_state.continuous_state['side'] >= device_state.side_threshold and 
                        current_time - device_state.last_notification_time['side'] >= device_state.side_threshold):
                        image_url = await upload_to_cloudinary(image_base64)
                        await send_notifications(
                            device_id, 
                            'side', 
                            device_state.continuous_state['side'],
                            device_state.start_time['side'],
                            image_url
                        )
                        device_state.last_notification_time['side'] = current_time
                else:
                    device_state.continuous_state['side'] = 0
                    device_state.start_time['side'] = None

                # Check for prone position
                if posture == 'prone':
                    if device_state.start_time['prone'] is None:
                        device_state.start_time['prone'] = current_time
                    device_state.continuous_state['prone'] = current_time - device_state.start_time['prone']
                    
                    if (device_state.continuous_state['prone'] >= device_state.prone_threshold and 
                        current_time - device_state.last_notification_time['prone'] >= device_state.prone_threshold):
                        image_url = await upload_to_cloudinary(image_base64)
                        await send_notifications(
                            device_id, 
                            'prone', 
                            device_state.continuous_state['prone'],
                            device_state.start_time['prone'],
                            image_url
                        )
                        device_state.last_notification_time['prone'] = current_time
                else:
                    device_state.continuous_state['prone'] = 0
                    device_state.start_time['prone'] = None

                # Check for no blanket
                if not has_blanket:
                    if device_state.start_time['noBlanket'] is None:
                        device_state.start_time['noBlanket'] = current_time
                    device_state.continuous_state['noBlanket'] = current_time - device_state.start_time['noBlanket']
                    
                    if (device_state.continuous_state['noBlanket'] >= device_state.no_blanket_threshold and 
                        current_time - device_state.last_notification_time['noBlanket'] >= device_state.no_blanket_threshold):
                        image_url = await upload_to_cloudinary(image_base64)
                        await send_notifications(
                            device_id, 
                            'noBlanket', 
                            device_state.continuous_state['noBlanket'],
                            device_state.start_time['noBlanket'],
                            image_url
                        )
                        device_state.last_notification_time['noBlanket'] = current_time
                else:
                    device_state.continuous_state['noBlanket'] = 0
                    device_state.start_time['noBlanket'] = None

        except Exception as e:
            print(f"Error in WebSocket connection: {e}")
        finally:
            if device_id in self.devices:
                del self.devices[device_id]
