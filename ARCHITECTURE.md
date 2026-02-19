# SwiftChat Integration & PAL Architecture

**Status**: Design Complete
**Date**: Feb 2026

## 1. Core Integration (`tap_swiftchat`)
We are building a standalone Frappe App to connect TAP LMS to SwiftChat.

- **Outbound**: `swiftchat_integration.py` (API wrapper for `send_message`, `send_media`).
- **Inbound**: `swiftchat_webhook.py` (Receives JSON payloads).
- **Isolation**: Runs parallel to Glific. Does not modify core `tap_lms` logic initially.

## 2. Input Processing (The "Front Desk")
Given our user base (Low income, low literacy, regional languages), we prioritize **AI-First Input Understanding**.

- **Voice Layer**: Bhashini Integration (Audio -> Text).
- **Intent Layer**: LLM/SLM classifier to handle messy inputs ("Mala samjh nahi aaya").
  - *Input*: "Next video kab milega?"
  - *Output*: `Intent: CONTENT_REQUEST`, `Entity: VIDEO`.

## 3. Orchestration (The "State Machine")
We move from hardcoded Python logic to **Metadata-Driven Flows**.

- **`Interaction Node` (DocType)**: Defines a unit of content (Text/Video/Question). Replaces hardcoded Glific Flow IDs.
- **`StudentStageProgress` (Runtime)**: Enhanced to track granular node-level progress (`current_interaction_node`).
- **Logic**: A Python "Flow Engine" traverses the nodes based on user input.

## 4. Output Generation (Safety & Persona)
To ensure quality communication with students:

- **The Persona Engine**: Generates warm, localized responses ("Hey Champion!").
- **The Auditor Agent**: A final safety check before sending.
  - *Checks*: Safety, Tone, Complexity (Grade-appropriate language).
  - *Action*: Blocks inappropriate responses; logs failures for fine-tuning.

## 5. Personalized Adaptive Learning (PAL)
- **The Analyst**: Diagnoses *why* a student failed (Conceptual vs Calculation error).
- **The Navigator**: Decides the next step (Remedial Node vs Challenge Node) based on diagnosis.

## 6. Implementation Strategy
- **Phase 1**: `tap-swiftchat` app deployment (Basic Send/Receive).
- **Phase 2**: `Interaction Node` DocType & Metadata Migration.
- **Phase 3**: "Front Desk" AI Layer (Bhashini + Intent).
- **Phase 4**: "Auditor" Safety Layer.
