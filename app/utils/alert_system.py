"""
Alert system for dangerous baby postures.

This module provides functionality to generate and send alerts when dangerous
baby postures are detected.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
from pathlib import Path
import asyncio
from app.models.schemas import RiskLevel
from app.config import settings

logger = logging.getLogger(__name__)

class AlertSystem:
    """
    System for generating and dispatching alerts about dangerous baby postures.
    
    This class handles the creation, prioritization, and dispatch of alerts
    to configured notification channels.
    """
    
    # Define alert levels and their corresponding colors for UI
    ALERT_LEVELS = {
        RiskLevel.LOW: {"name": "info", "color": "blue", "priority": 1},
        RiskLevel.MEDIUM: {"name": "notice", "color": "yellow", "priority": 2},
        RiskLevel.HIGH: {"name": "warning", "color": "orange", "priority": 3},
        RiskLevel.CRITICAL: {"name": "emergency", "color": "red", "priority": 4},
    }
    
    def __init__(self, 
                alert_threshold: Optional[float] = None, 
                alert_history_file: Optional[str] = None):
        """
        Initialize the alert system.
        
        Args:
            alert_threshold: Minimum risk score to trigger alerts (default from settings)
            alert_history_file: Path to file for storing alert history
        """
        self.alert_threshold = alert_threshold or settings.ALERT_THRESHOLD
        self.alert_history_file = alert_history_file or str(Path(settings.LOG_DIR) / "alert_history.json")
        self._ensure_alert_history_file()
        
    def _ensure_alert_history_file(self):
        """Ensure the alert history file exists."""
        alert_history_dir = os.path.dirname(self.alert_history_file)
        os.makedirs(alert_history_dir, exist_ok=True)
        
        if not os.path.exists(self.alert_history_file):
            with open(self.alert_history_file, 'w') as f:
                json.dump([], f)
    
    async def process_analysis(
        self,
        pose_type: str,
        risk_level: RiskLevel,
        risk_score: float,
        analysis: Dict[str, Any],
        image_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process analysis results and generate alerts if needed.
        
        Args:
            pose_type: Detected pose type
            risk_level: Determined risk level
            risk_score: Numerical risk score (0-10)
            analysis: Detailed posture analysis
            image_path: Path to annotated image if available
            
        Returns:
            Alert information if generated, empty dict otherwise
        """
        # Check if risk score exceeds threshold for alerting
        if risk_score < self.alert_threshold:
            logger.debug(f"Risk score {risk_score} below threshold {self.alert_threshold}, no alert")
            return {}
        
        # Generate alert content
        alert = self.generate_alert(pose_type, risk_level, risk_score, analysis, image_path)
        
        # Save alert to history
        await self.save_alert(alert)
        
        # Dispatch alert through configured channels
        await self.dispatch_alert(alert)
        
        return alert
    
    def generate_alert(
        self,
        pose_type: str,
        risk_level: RiskLevel,
        risk_score: float,
        analysis: Dict[str, Any],
        image_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate alert content based on analysis results.
        
        Args:
            pose_type: Detected pose type
            risk_level: Determined risk level
            risk_score: Numerical risk score (0-10)
            analysis: Detailed posture analysis
            image_path: Path to annotated image if available
            
        Returns:
            Alert information dictionary
        """
        # Get alert level information
        alert_level = self.ALERT_LEVELS.get(risk_level, 
                                          self.ALERT_LEVELS[RiskLevel.MEDIUM])
        
        # Generate title based on pose type and risk level
        title_mapping = {
            "face_down": "Baby Face Down - {level} Alert",
            "lying_on_stomach": "Baby Lying on Stomach - {level} Alert",
            "lying_on_side": "Baby Lying on Side - {level} Notice",
            "limbs_folded": "Baby's Limbs Folded - {level} Notice",
            "lying_on_back": "Baby Lying on Back - {level} Information"
        }
        
        title = title_mapping.get(
            pose_type, 
            "Baby Posture Alert - {level}"
        ).format(level=alert_level["name"].capitalize())
        
        # Generate message based on safety concerns
        safety_concerns = analysis.get("safety_concerns", [])
        concern_messages = {
            "face_pressed_against_surface": "Baby's face is pressed against the surface!",
            "face_partially_obstructed": "Baby's face is partially obstructed.",
            "prone_position_breathing_risk": "Prone position poses breathing risks.",
            "restricted_arm_movement": "Baby's arm movement appears restricted.",
            "restricted_leg_movement": "Baby's leg movement appears restricted.",
            "temperature_regulation": "Baby may have kicked off blankets."
        }
        
        message_parts = [concern_messages.get(concern, "") 
                         for concern in safety_concerns if concern in concern_messages]
        if not message_parts:
            message_parts = ["Baby's posture requires attention."]
        
        message = " ".join(message_parts)
        
        # Generate recommendations text
        recommendations = analysis.get("recommendations", [])
        recommendation_text = ". ".join(r.replace("_", " ").capitalize() 
                                      for r in recommendations)
        if recommendation_text:
            recommendation_text += "."
        
        # Create the alert object
        alert = {
            "id": f"alert_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "title": title,
            "message": message,
            "recommendations": recommendation_text,
            "level": alert_level["name"],
            "color": alert_level["color"],
            "priority": alert_level["priority"],
            "pose_type": pose_type,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "image_path": image_path
        }
        
        return alert
    
    async def save_alert(self, alert: Dict[str, Any]):
        """
        Save alert to history file.
        
        Args:
            alert: Alert information dictionary
        """
        try:
            # Read existing alerts
            with open(self.alert_history_file, 'r') as f:
                alerts = json.load(f)
            
            # Add new alert
            alerts.append(alert)
            
            # Keep only the last 100 alerts
            alerts = alerts[-100:]
            
            # Write back to file
            with open(self.alert_history_file, 'w') as f:
                json.dump(alerts, f, indent=2)
                
            logger.debug(f"Alert saved to history: {alert['id']}")
        except Exception as e:
            logger.error(f"Error saving alert to history: {e}")
    
    async def dispatch_alert(self, alert: Dict[str, Any]):
        """
        Dispatch alert through configured notification channels.
        
        Args:
            alert: Alert information dictionary
        """
        # Log the alert
        log_level = logging.WARNING if alert["priority"] >= 3 else logging.INFO
        logger.log(log_level, f"ALERT: {alert['title']} - {alert['message']}")
        
        # Dispatch to configured notification channels
        tasks = []
        
        # Only add notification tasks if they're configured
        if hasattr(settings, 'ENABLE_PUSH_NOTIFICATIONS') and settings.ENABLE_PUSH_NOTIFICATIONS:
            tasks.append(self._send_push_notification(alert))
        
        if hasattr(settings, 'ENABLE_SMS_ALERTS') and settings.ENABLE_SMS_ALERTS:
            # Only send SMS for high priority alerts
            if alert["priority"] >= 3:
                tasks.append(self._send_sms(alert))
        
        if hasattr(settings, 'ENABLE_EMAIL_ALERTS') and settings.ENABLE_EMAIL_ALERTS:
            tasks.append(self._send_email(alert))
        
        # Execute all notification tasks concurrently
        if tasks:
            await asyncio.gather(*tasks)
    
    async def _send_push_notification(self, alert: Dict[str, Any]):
        """
        Send push notification (placeholder implementation).
        
        In a real implementation, this would use a service like Firebase Cloud Messaging,
        OneSignal, or similar to send push notifications to mobile devices.
        
        Args:
            alert: Alert information dictionary
        """
        logger.info(f"PUSH NOTIFICATION would be sent: {alert['title']}")
        # In a real implementation, this would make an API call to the push notification service
    
    async def _send_sms(self, alert: Dict[str, Any]):
        """
        Send SMS alert (placeholder implementation).
        
        In a real implementation, this would use a service like Twilio, Nexmo,
        or similar to send SMS messages.
        
        Args:
            alert: Alert information dictionary
        """
        logger.info(f"SMS would be sent: {alert['title']}")
        # In a real implementation, this would make an API call to the SMS service
    
    async def _send_email(self, alert: Dict[str, Any]):
        """
        Send email alert (placeholder implementation).
        
        In a real implementation, this would use an email service or SMTP server
        to send email notifications.
        
        Args:
            alert: Alert information dictionary
        """
        logger.info(f"EMAIL would be sent: {alert['title']}")
        # In a real implementation, this would send an email
