# Technical Specification: TAP State Machine & Learning Engine

**Status**: Draft
**Version**: 1.0
**Context**: Powering Personalized Adaptive Learning (PAL) via SwiftChat.

## 1. Data Architecture

### 1.1 The Content Graph (`Interaction Node`)
Represents a unit of interaction. Replaces hardcoded flows.

| Field | Type | Description |
| :--- | :--- | :--- |
| `name` | Data | Unique ID (e.g., `math_q1_fractions`). |
| `type` | Select | `Content` (Video/Text), `Assessment` (Quiz), `Menu` (Branching). |
| `content_payload` | JSON | `{"text": "...", "media": "...", "options": [...]}`. |
| `validation_rules` | JSON | Regex or logic to validate input (e.g., `{"pattern": "^[0-9]+$"}`). |
| **`routes`** | JSON | Defines the edges. `{"success": "node_b", "failure": "DYNAMIC:NAVIGATOR"}`. |
| `pal_tags` | Link | Links to `Learning Objective` (e.g., `fractions`). |

### 1.2 The Event Stream (`Interaction Log`)
Immutable record of every user action. The "Raw Data".

| Field | Type | Description |
| :--- | :--- | :--- |
| `student` | Link | Student ID. |
| `node` | Link | Interaction Node ID. |
| `timestamp` | Datetime | Server time. |
| `input_raw` | Text | What the user typed/said. |
| `is_correct` | Check | Auto-graded result. |
| `time_taken` | Float | Seconds since node was sent. |
| **`analyst_diagnosis`** | JSON | Populated by Analyst Agent (e.g., `{"error_type": "conceptual"}`). |

### 1.3 The User Model (`Student Knowledge State`)
Aggregated profile used for decision making.

| Field | Type | Description |
| :--- | :--- | :--- |
| `student` | Link | Student ID. |
| `mastery_map` | JSON | `{"fractions": 0.4, "algebra": 0.8}`. |
| `active_gaps` | JSON | List of undiagnosed misconceptions. |
| `current_node` | Link | Where they are RIGHT NOW. |
| `path_history` | Text | Sequence of visited Node IDs. |

## 2. The Flow Engine (`FlowEngine.py`)

### 2.1 Main Loop
```python
def process_input(user_id, input_text):
    # 1. Load Context
    state = get_student_state(user_id)
    current_node = get_node(state.current_node)

    # 2. Global Interrupts (Safety Brake)
    if input_text in ["STOP", "HELP"]:
        return trigger_global_handler(input_text)

    # 3. Validation & Grading
    is_valid, is_correct = validate_and_grade(current_node, input_text)
    
    # 4. Log Interaction
    log_id = create_interaction_log(user_id, current_node, input_text, is_correct)

    # 5. Determine Next Step
    if is_correct:
        next_node_id = resolve_route(current_node.routes['success'])
    else:
        # Trigger Analyst Agent (Async)
        enqueue_analyst_job(log_id)
        # Ask Navigator for path
        if current_node.routes['failure'] == "DYNAMIC:NAVIGATOR":
            next_node_id = navigator_agent.decide(state, log_id)
        else:
            next_node_id = current_node.routes['failure']

    # 6. Execute Transition
    update_state(user_id, next_node_id)
    return render_node(next_node_id)
```

## 3. Agent Integration Points

### 3.1 The Analyst (Async Diagnosis)
- **Trigger**: `Interaction Log` created with `is_correct=False`.
- **Input**: `input_raw`, `node.content`.
- **Action**: LLM Analysis.
- **Output**: Updates `Interaction Log.analyst_diagnosis` + Updates `Student Knowledge State`.

### 3.2 The Navigator (Real-time Pathing)
- **Trigger**: `FlowEngine` hits a `DYNAMIC` route.
- **Input**: `Student Knowledge State`.
- **Action**: `if gap_detected: return remedial_node else: return next_standard_node`.

## 4. Migration Strategy
1.  **Phase 1**: Deploy DocTypes.
2.  **Phase 2**: Port existing Glific flows to `Interaction Node` format (Linear paths).
3.  **Phase 3**: Enable "Analyst" logging (Shadow mode).
4.  **Phase 4**: Enable "Navigator" dynamic routing.
