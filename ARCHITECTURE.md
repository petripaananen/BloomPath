# BloomPath System Architecture

This document provides a high-level overview of the BloomPath system, illustrating the component hierarchy and the data flow between them.

## 1. Component Hierarchy

BloomPath is composed of a Python middleware layer that orchestrates communication between external services (Jira, AI Models) and the visualization engine (Unreal Engine 5).

```mermaid
classDiagram
    class Middleware {
        +Flask App
        +Webhook Handler
        +Jira Integration
        +sync_initial_state()
        +process_webhook()
    }

    class BloomPathOrchestrator {
        +PWM Loop Manager
        +process_ticket()
        +inject_tags()
    }

    class AI_Clients {
        <<Interface>>
    }

    class WorldLabsClient {
        +generate_world()
    }

    class SemanticAnalyzer {
        +analyze_world()
        +Gemini Vision
    }

    class UE5Interface {
        +Remote Control API
        +trigger_ue5_growth()
        +trigger_ue5_weather()
        +trigger_ue5_spawn_avatar()
    }

    Middleware --> BloomPathOrchestrator : Uses
    Middleware --> UE5Interface : Direct Control (Growth/Weather)
    BloomPathOrchestrator --> WorldLabsClient : 1. Synthesize
    BloomPathOrchestrator --> SemanticAnalyzer : 2. Tag
    BloomPathOrchestrator --> UE5Interface : 3. Inject
    AI_Clients <|-- WorldLabsClient
    AI_Clients <|-- SemanticAnalyzer
```

---

## 2. Data Flow: The Project World Model (PWM) Loop

This diagram illustrates how an abstract Jira Ticket is transformed into a validated 3D Environment.

```mermaid
sequenceDiagram
    participant Jira as Linear / Jira
    participant Mid as Middleware (Python)
    participant Orch as Orchestrator
    participant Marble as World Labs (Marble)
    participant Gemini as Google Gemini
    participant UE5 as Unreal Engine 5

    Note over Jira, UE5: Phase 1: Intent to Spatial

    Jira->>Mid: Webhook (Issue Updated)
    Mid->>Orch: process_ticket(issue_data)
    
    Orch->>Orch: Parse Intent (Prompt)
    
    Orch->>Marble: generate_world(prompt)
    Marble-->>Orch: Returns .gltf + Image
    
    Note over Jira, UE5: Phase 2: Semantic Injection

    Orch->>Gemini: analyze_world(Image)
    Gemini-->>Orch: World Manifest (JSON)
    Orch->>UE5: Inject Semantic Tags (RCP)

    Note over Jira, UE5: Phase 3: Real-time Growth

    Mid->>UE5: trigger_growth(param)
    UE5->>UE5: Update Garden State
```

---

## 3. Data Flow: Environmental Dynamics

How project health translates to environmental weather.

```mermaid
flowchart TD
    JIRA[Jira Board] -->|Fetch Sprint Data| MID[Middleware]
    MID -->|Calculate Progress %| TIME[Time of Day]
    MID -->|Calculate Health (Blockers/Done)| WEATHER[Weather State]
    
    TIME -->|RCP: set_sun_position| UE5[Unreal Engine 5]
    WEATHER -->|RCP: set_weather_type| UE5
    
    subgraph UE5_Logic
        UE5 --> SUN[Sun & Sky Actor]
        UE5 --> NIAGARA[Rain/Storm Systems]
    end
```
