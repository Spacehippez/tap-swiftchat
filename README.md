# SwiftChat Integration Specification (DRAFT)

**Feature**: Multi-Channel Messaging Support (Glific + SwiftChat)
**Status**: Proposed
**Owner**: Rig (Frappe Architect)

## 1. Overview
TAP LMS currently supports WhatsApp via Glific. We are adding SwiftChat as a parallel channel. The goal is to allow students/teachers to interact with TAP via either platform seamlessly.

## 2. DocType Changes

### 2.1. `SwiftChat Settings` (Single DocType)
- **Purpose**: Configure API credentials.
- **Fields**:
  - `api_key` (Password): Authentication token.
  - `base_url` (Data): API endpoint (e.g., `https://api.swiftchat.ai/v1`).
  - `bot_id` (Data): Unique Bot ID.
  - `webhook_secret` (Password): Verify incoming payloads.
  - `enabled` (Check): Toggle integration.

### 2.2. `Student` & `Teacher` (DocType Extensions)
- **Current State**: `glific_id` (Data) stores the Glific contact ID.
- **Proposed Change**: Add `swiftchat_id` (Data, Unique, Index).
  - *Alternative*: Migrate to a child table `Contact Channels` (`channel_type`, `channel_id`) to support N channels in future. For MVP, adding a field is faster.

## 3. Python Module Structure

### 3.1. `swiftchat_integration.py` (Outbound)
- **Role**: The API Client.
- **Key Functions**:
  - `send_message(user_id, text)`: Standard text.
  - `send_media(user_id, media_url, caption)`: Images/Video.
  - `send_buttons(user_id, text, buttons)`: Interactive menus.
  - `get_contact_profile(user_id)`: Fetch name/metadata.

### 3.2. `swiftchat_webhook.py` (Inbound)
- **Role**: The Event Listener.
- **Endpoint**: `/api/method/tap_lms.swiftchat_webhook.handle_incoming`
- **Logic**:
  1. Verify Signature (`X-SwiftChat-Signature`).
  2. Parse JSON Payload.
  3. Extract `sender_id` and `message_type`.
  4. Route to Business Logic (`process_student_message` or `process_teacher_message`).

## 4. Abstraction Layer (The "Unified Messenger")

To avoid `if glific: else swiftchat:` spaghetti code in `api.py`, we need a unified interface.

**Proposed Interface (`messaging_utils.py`):**
```python
def send_unified_message(user_doc, message_text):
    """
    Sends message to the user on their active channel.
    """
    if user_doc.preferred_channel == 'SwiftChat' and user_doc.swiftchat_id:
        swiftchat_integration.send_message(user_doc.swiftchat_id, message_text)
    elif user_doc.glific_id:
        glific_integration.send_message(user_doc.glific_id, message_text)
    else:
        frappe.log_error(f"User {user_doc.name} has no valid messaging channel")
```

## 5. Migration Strategy
1. **Create Settings**: Deploy `SwiftChat Settings`.
2. **Update Schema**: Add `swiftchat_id` to `Student`/`Teacher`.
3. **Deploy Webhook**: Expose the endpoint and configure SwiftChat console.
4. **Test Flow**: Send "Hi" from SwiftChat -> Verify response.

## 6. Open Questions
- Does SwiftChat support "Template Messages" like WhatsApp HSM? If so, we need a template mapping DocType.
- How do we handle "Session Expiry"? (24-hour window rules?)
