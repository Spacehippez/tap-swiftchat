# tap_lms/swiftchat_integration.py
import frappe
import requests
import json
from frappe.utils import cstr

def get_swiftchat_settings():
    """Fetch SwiftChat configuration from single DocType."""
    return frappe.get_single("SwiftChat Settings")

def send_message(user_id, message_text, buttons=None):
    """
    Send a text message (optionally with buttons) to a SwiftChat user.
    """
    settings = get_swiftchat_settings()
    if not settings.enabled:
        return {"status": "skipped", "message": "SwiftChat integration disabled"}

    headers = {
        "Authorization": f"Bearer {settings.get_password('api_key')}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "to": user_id,
        "type": "text",
        "text": {"body": message_text}
    }

    if buttons:
        payload["type"] = "interactive"
        payload["interactive"] = {
            "type": "button",
            "body": {"text": message_text},
            "action": {"buttons": buttons} 
            # Buttons format: [{"type": "reply", "reply": {"id": "btn1", "title": "Yes"}}]
        }

    try:
        response = requests.post(
            f"{settings.base_url}/messages", 
            json=payload, 
            headers=headers, 
            timeout=10
        )
        response.raise_for_status()
        return {"status": "success", "response": response.json()}
    
    except requests.exceptions.RequestException as e:
        frappe.log_error(f"SwiftChat Send Error: {str(e)}", "SwiftChat Integration")
        return {"status": "error", "message": str(e)}

def send_media(user_id, media_url, caption=None, media_type="image"):
    """
    Send media (image/video/document) to a SwiftChat user.
    """
    settings = get_swiftchat_settings()
    if not settings.enabled:
        return

    headers = {
        "Authorization": f"Bearer {settings.get_password('api_key')}",
        "Content-Type": "application/json"
    }

    payload = {
        "to": user_id,
        "type": media_type,
        media_type: {"link": media_url}
    }
    
    if caption:
        payload[media_type]["caption"] = caption

    try:
        requests.post(
            f"{settings.base_url}/messages", 
            json=payload, 
            headers=headers, 
            timeout=30
        )
    except Exception as e:
        frappe.log_error(f"SwiftChat Media Error: {str(e)}", "SwiftChat Integration")

def get_contact_profile(user_id):
    """
    Fetch user profile metadata (Name, Status) from SwiftChat.
    """
    settings = get_swiftchat_settings()
    headers = {"Authorization": f"Bearer {settings.get_password('api_key')}"}
    
    try:
        res = requests.get(
            f"{settings.base_url}/contacts/{user_id}", 
            headers=headers,
            timeout=5
        )
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return None
