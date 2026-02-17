# tap_lms/messaging_utils.py
import frappe
from tap_lms.glific_integration import send_message as send_glific
from tap_lms.swiftchat_integration import send_message as send_swiftchat

def send_unified_message(user_doc, message_text, buttons=None):
    """
    Sends message to the user on their active channel.
    user_doc: Student or Teacher DocType.
    """
    # 1. Check for SwiftChat ID
    if user_doc.swiftchat_id:
        return send_swiftchat(user_doc.swiftchat_id, message_text, buttons)
    
    # 2. Check for Glific ID (Fallback)
    elif user_doc.glific_id:
        # Glific message sending logic here (adapt arguments as needed)
        return send_glific(user_doc.glific_id, message_text)
    
    else:
        frappe.log_error(f"User {user_doc.name} has no valid messaging channel", "Unified Messenger")
        return {"status": "skipped", "message": "No valid channel"}
