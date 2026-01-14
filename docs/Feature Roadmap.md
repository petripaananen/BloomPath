# BloomPath Feature Roadmap

This roadmap outlines the evolution of the BloomPath digital twin, from foundational infrastructure to advanced AI simulations.

---

## Phase 1: Middleware & Initial Sync ✅
The foundation of BloomPath involves the core logic engine and Jira connectivity.
- **Jira Integration**: Configuration of API access and environment settings.
- **Webhook Listener**: Implementation of a robust engine for real-time issue updates.
- **State Synchronization**: Mechanisms to ensure the garden reflects current project status on startup.
- **Connectivity**: Establishing communication between the Python middleware and Unreal Engine 5.

---

## Phase 2: UE5 Visual Foundations ✅
This phase established the visual language and lifecycle of the 3D garden.
- **Grower Actor**: Development of the core Blueprint logic for plant growth.
- **Mesh Spawning**: Implementation of high-fidelity 3D mesh placement in the world.
- **ID Tagging**: System for tracking and managing individual tasks within the engine.
- **Growth Rollback**: Creating logic to handle reopened tasks or status reversals.

---

## Phase 3: Environmental Dynamics ✅
Connecting the garden's atmosphere to overall sprint health and velocity.

### Sprint Weather System
- **Real-time Metrics**: Querying Jira for sprint burndown and velocity data.
- **Health Mapping**: Calculating team progress to determine environmental states.
- **Weather States**: A dynamic system ranging from **Sunny** (On Track) to **Stormy** (Behind Schedule).
- **Particle Systems**: Integration of Niagara effects for rain and atmospheric lighting.

### Time-of-Day Mapping
- **Sprint Clock**: Mapping the current stage of the sprint to a 24-hour cycle.
- **Visual Milestones**: **Dawn** represents the sprint start, while **Sunset** indicates the deadline.
- **Dynamic Lighting**: Engine lighting that reacts to current progress.

---

## Phase 4: Social Layer
Bringing team identity and presence into the Digital Twin of Organization.

### Team Member Avatars
- **Assignee Metadata**: Identifying owners of tasks via the Jira API.
- **Gardener NPCs**: Creating representative characters for team members.
- **Task Spawning**: Placing avatars near their assigned work areas in the garden.
- **Social Interaction**: Shared animations for task completion and maintenance.

---

## Phase 5: Audio Feedback
Enhancing immersion through a reactive and evocative soundscape.

### Ambient Soundscape
- **Success Chimes**: Pleasing audio cues for task completion and successes.
- **Productivity Intensity**: Birdsong and nature sounds tied to the count of **Done** issues.
- **Risk Notification**: Ominous ambient tones for blockers or critical-path delays.

---

## Phase 6: Historical Visualization
The ability to navigate through the project’s growth history and organizational evolution.

### Garden Time Machine
- **State Snapshots**: Persistent storage of garden configurations at specific milestones.
- **Interactive Timeline**: A user-friendly time slider for scrubbing through history.
- **Evolution Playback**: Animated visualization of growth patterns across multiple sprints.

---

## Phase 7: Scale & Multi-Project
Expanding BloomPath to cover complex, organization-wide ecosystems.

### Multi-Project Gardens
- **Cross-Project Ingestion**: Simultaneously querying data from multiple Jira projects.
- **Ecosystem Zones**: Distinct garden regions and unique aesthetics for different teams.
- **Executive Dashboard**: A sprawling organizations-wide view visualized as a connected landscape.

---

## Phase 8: What-If Scenarios (Thesis Core)
In the context of **AI World Models**, these scenarios act as **Latent Forecasters**—allowing the system to "dream" potential futures based on organizational constraints.

### The "What-If" Simulation Roadmap
- **Phase A: Resource Stress-Testing**: Visualizing the impact of losing staff through narrowing paths and slowing growth.
- **Phase B: Scope Creep Simulation**: Showing over-encumbered trees and withered leaves to represent excessive load.
- **Phase C: Priority Shifting**: Rerouting "Pollinator Fireflies" to visualize resource reallocation impact.
- **Phase D: Environmental Risks**: Localized storms appearing over integration zones during failed dependency simulations.

### Technical Implementation: The Sandbox Mode
- **Snapshot State**: Local Jira caching for non-destructive "what-if" testing.
- **Prediction Engine**: Python Middleware AI model for forecasting outcomes.
- **Ghost Garden**: Semi-transparent holographic overlays in Unreal Engine.

---

## Priority Matrix

| Feature | Impact | Effort | Thesis Value |
|---------|--------|--------|--------------|
| **What-If Scenarios** | Very High | High | ⭐⭐⭐⭐⭐ |
| **Weather System** | High | Medium | ⭐⭐⭐ |
| **Audio Feedback** | Medium | Low | ⭐⭐ |
| **Team Avatars** | High | High | ⭐⭐⭐ |
| **Time Machine** | High | High | ⭐⭐⭐ |
| **Multi-Project** | Medium | High | ⭐⭐ |

---

## Quick Wins ⚡

- **Audio Feedback** — Adds immediate immersion with minimal implementation overhead.
- **Time-of-Day** — Leverages native lighting for instant visual impact.
- **Weather Particles** — Uses existing templates for rapid environment polish.
