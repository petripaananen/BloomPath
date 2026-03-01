# BloomPath Technical Architecture

BloomPath is an AI-enhanced bridge application connecting agile project management tools with real-time 3D simulation in Unreal Engine 5. The primary purpose of the architecture is to visually and interactively represent software engineering tasks as organic elements inside a virtual "Garden".

## System Components

1.  **Project Data Sources**
    *   **Linear & Jira**: The raw data ingress point (CRITICAL: You MUST use the official Linear app logo and Atlassian Jira software logo for these, not generic software icons). These services send HTTP POST Webhook Events to the middleware.
    
2.  **BloomPath Middleware (Python Flask)**
    *   **Webhook Receiver**: Ingests raw JSON payloads from the project management tools.
    *   **Data Normalizer**: Standardizes the disparate ticket formats into a Unified Ticket representation.
    *   **Event Queue**: A buffer regulating the flow of new Unified Tickets.
    *   **Core Orchestrator**: The central brain driving the business logic and managing the state. It handles events popped from the queue.

3.  **AI Generation & Analysis Layer**
    *   The Core Orchestrator sends context prompts (like feature requests from tickets) to **World Labs Marble**, which synchronously generates `.GLB` 3D model assets.
    *   A quality validation requests and spatial planning metadata are processed by **Gemini 3 Flash (Vision Validation)**, which returns semantic layout and navigation JSON to the Orchestrator.
    *   The architectural state is periodically fed to **DiagramAgent (Multi-Agent Architect)** to update the documentation.

4.  **Engine Presentation Layer**
    *   **The Garden (Unreal Engine 5.7)**: Receives remote API commands (Spawn, Scale, Adjust Weather) from the Core Orchestrator.
    *   **Local Client Simulation**: Represents the end-user interacting with the UE5 Garden (e.g., watering a plant). Object interaction sync operations are sent back to the Webhook Receiver to trigger return mutations (resolving an incident in Linear/Jira).

## The Data Flow Loop
The workflow follows a cyclic pattern: Data comes from Data Sources to Middleware, get augmented by AI Generation, gets rendered in the Engine Presentation Layer, and then client interaction feedback updates the original Data Sources.
