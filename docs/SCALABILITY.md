# Scalable Architecture for 100k Users

**Strategy**: Decouple the real-time chat loop (Redis) from the heavy persistence/AI loop (RabbitMQ + MariaDB).

```mermaid
graph TD
    subgraph "Client Layer"
        User[Student (100k Concurrent)]
        SwiftChat[SwiftChat Platform]
    end

    subgraph "Fast Lane (Synchronous / <100ms)"
        Webhook[Webhook Handler (Gunicorn)]
        FlowEngine[Flow Engine Logic]
        Redis[(Redis Cache)]
        
        User -->|Message| SwiftChat
        SwiftChat -->|Webhook| Webhook
        Webhook -->|Process| FlowEngine
        FlowEngine <-->|Get/Set State| Redis
        FlowEngine -->|Reply| SwiftChat
    end

    subgraph "Async Bus"
        RMQ{RabbitMQ Queue}
        FlowEngine -.->|Publish Event| RMQ
    end

    subgraph "Slow Lane (Asynchronous Workers)"
        Worker[Python Worker]
        DB[(MariaDB / Frappe)]
        Analyst[Analyst Agent (LLM)]
        Navigator[Navigator Agent (Logic)]

        RMQ -->|Consume| Worker
        Worker -->|Write Log| DB
        Worker -->|Call| Analyst
        Worker -->|Call| Navigator
        
        Navigator -->|Pre-compute Next Steps| Redis
    end

    %% Key Data Flows
    linkStyle 4,5,6 stroke:#0f0,stroke-width:2px; %% Fast Path
    linkStyle 8 stroke:#f00,stroke-width:2px,stroke-dasharray: 5 5; %% Async Handoff
```

## Data Flow Description

1.  **Fast Lane (The Chat)**:
    - User says "5".
    - `FlowEngine` checks Redis: "User is at Q1".
    - `FlowEngine` validates "5".
    - `FlowEngine` updates Redis: "User moved to Q2".
    - `FlowEngine` sends "Correct! Next question..." to SwiftChat.
    - **Time**: ~50ms.

2.  **Async Lane (The Brain)**:
    - `FlowEngine` pushes event to RabbitMQ: `{"user": 123, "node": "q1", "answer": "5", "correct": true}`.
    - **Worker** picks up event.
    - **Worker** saves to `Interaction Log` (MariaDB).
    - **Worker** updates `Student Knowledge State` (MariaDB).
    - **Navigator** checks mastery -> Decides next 3 steps -> **Writes to Redis** (`next_nodes` list).

## Critical Optimizations
- **Session State**: Lives entirely in Redis. If MariaDB goes down, chat continues (until Redis cache runs out).
- **Pre-Computation**: The Navigator calculates the *future* path while the student is reading the *current* message.
