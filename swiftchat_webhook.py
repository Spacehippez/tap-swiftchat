# tap_lms/swiftchat_webhook.py
import frappe
from frappe import _
from werkzeug.wrappers import Response
import json
from datetime import datetime

# Import business logic
from tap_lms.swiftchat_integration import send_message, get_contact_profile
from tap_lms.api import create_new_student # Or generic method

@frappe.whitelist(allow_guest=True)
def handle_incoming_message():
    """
    Endpoint: /api/method/tap_lms.swiftchat_webhook.handle_incoming
    Receives incoming webhook payloads from SwiftChat.
    """
    
    # 1. Basic Security Check (Optional: Verify Signature)
    # verify_webhook_signature(frappe.request.headers)

    # 2. Parse Payload
    try:
        data = frappe.request.get_json() or {}
        messages = data.get("entry", [])[0].get("changes", [])[0].get("value", {}).get("messages", [])
        
        if not messages:
            return Response("OK", status=200)

        for msg in messages:
            sender_id = msg.get("from")
            msg_type = msg.get("type")
            timestamp = msg.get("timestamp")
            
            # Handle Text
            if msg_type == "text":
                text_body = msg.get("text", {}).get("body")
                process_user_message(sender_id, text_body)
                
            # Handle Buttons (Interactive)
            elif msg_type == "interactive":
                btn_reply = msg.get("interactive", {}).get("button_reply", {})
                btn_id = btn_reply.get("id")
                btn_title = btn_reply.get("title")
                process_user_button(sender_id, btn_id, btn_title)
                
            # Handle Media (Optional)
            elif msg_type == "image":
                # Handle image submission logic
                pass

        return Response("EVENT_RECEIVED", status=200)
    
    except Exception as e:
        frappe.log_error(f"SwiftChat Webhook Error: {str(e)}", "SwiftChat Webhook")
        return Response("Error", status=500)

def process_user_message(sender_id, text):
    """
    Route message to appropriate handler (Student/Teacher/Generic).
    """
    # 1. Identify User
    student = frappe.db.get_value("Student", {"swiftchat_id": sender_id}, ["name", "name1"], as_dict=True)
    teacher = frappe.db.get_value("Teacher", {"swiftchat_id": sender_id}, ["name", "first_name"], as_dict=True)

    if student:
        # Existing Student Logic
        # e.g., tap_lms.student_flow.handle_message(student.name, text)
        frappe.log_error(f"Student {student.name1} sent: {text}", "SwiftChat Flow")
        
    elif teacher:
        # Existing Teacher Logic
        frappe.log_error(f"Teacher {teacher.first_name} sent: {text}", "SwiftChat Flow")
        
    else:
        # New User -> Onboarding Flow
        start_onboarding(sender_id)

def start_onboarding(sender_id):
    """
    Trigger the first step of onboarding via SwiftChat.
    """
    # Send Welcome Message
    welcome_text = "Welcome to TAP! Are you a Student or a Teacher?"
    buttons = [
        {"type": "reply", "reply": {"id": "role_student", "title": "Student"}},
        {"type": "reply", "reply": {"id": "role_teacher", "title": "Teacher"}}
    ]
    send_message(sender_id, welcome_text, buttons)

def process_user_button(sender_id, button_id, button_title):
    """
    Handle button clicks from interactive messages.
    """
    if button_id == "role_student":
        send_message(sender_id, "Great! What is your name?")
        # Update session state: "waiting_for_name"
        
    elif button_id == "role_teacher":
        send_message(sender_id, "Hello Teacher! Please enter your school code.")
