# 🌸 BloomPath: The Garden of Productivity

**BloomPath** is a sophisticated **Digital Twin of Organization (DTO)** that transforms abstract project management data into a living, breathing 3D ecosystem. By synchronizing **Jira** workflows with **Unreal Engine 5**, it creates a "Garden of Productivity" where project health is visualized through organic growth and environmental dynamics.

Developed as a proof-of-concept manifestation of the research themes explored in the Master’s Thesis: **"Emergent Workflows in the Video Game Industry: Leveraging AI World Models as a Framework for Production Management"**, BloomPath pushes the boundaries of data visualization by moving beyond 2D dashboards into immersive, interactive, and AI-validated spatial environments.

---

## 🚀 Key Innovation: The PWM Pipeline (v2.0)

BloomPath features the **Project World Model (PWM)** loop—a state-of-the-art pipeline that automates the creation and validation of spatial data twins:

1.  **Intent Parsing**: Automatically extracts design prompts and gameplay mechanics from Jira tickets.
2.  **Spatial Synthesis (Marble AI)**: Theoretically generates 3D world segments directly from project requirements.
3.  **Dynamic Simulation (Genie 3)**: Uses Google’s Genie 3 to simulate gameplay within the generated world, acting as an AI "QC agent" to ensure the generated space meets the functional requirements.
4.  **Semantic Tagging**: Leverages **Gemini** to analyze the visual output, applying rich metadata (physics, navigation, interaction) to UE5 actors automatically.

---

## 🌿 The Garden of Productivity

### **Real-time Growth Visualization**
*   **Issues as Plants**: When a Jira issue moves to "Done," a new branch or leaf grows in the UE5 garden.
*   **Organic Metadata**: Priority level dictates growth scale; Epic association determines color palettes.
*   **Blocker Thorns**: Blocked or high-impediment issues manifest as thorns, visually signaling bottlenecks in the workflow.

### **Environmental Dynamics (Sprint Weather)**
The garden's atmosphere is a literal reflection of **Sprint Health**:
*   ☀️ **Sunny**: High velocity, tasks on track.
*   ☁️ **Cloudy**: Approaching deadlines, minor blockers.
*   ⛈️ **Stormy**: Critically behind schedule or high volume of blocked issues.
*   🌅 **Time-of-Day**: The sun's position maps directly to sprint progress (Dawn = Start, Sunset = End).

---

## 🕹️ Interactive DTO (Bidirectional Sync)

BloomPath isn't just a display; it's a bridge:
*   **Watering Interaction**: Players can interact with plants in UE5 (e.g., using a watering can). Successful interaction triggers a back-sync to Jira, transitioning the corresponding issue to "Done."
*   **Audio Feedback**: Context-aware spatial audio events triggered by project updates.

---

## 🛠️ Technology Stack

*   **Engine**: Unreal Engine 5.5+ (Remote Control API, Niagara)
*   **Middleware**: Python (Flask, Requests, Threading)
*   **AI Models**: 
    *   **Genie 3**: World simulation and mechanics validation.
    *   **Gemini**: Semantic world analysis.
    *   **World Labs / Marble**: Spatial synthesis.
*   **Integrations**: Jira Cloud API (Webhooks), ngrok (Webhook exposure).
*   **Infrastructure**: Docker & Docker Compose support.

---

## 📂 Project Structure

*   `middleware.py`: The core hub managing webhooks, Jira logic, and UE5 commands.
*   `orchestrator.py`: Manages the iterative PWM generation/validation loop.
*   `ue5_interface.py`: Handles all RCP (Remote Control Protocol) communication with Unreal.
*   `genie_client.py` & `validation_agent.py`: Interfaces for AI-driven simulation and feedback.
*   `semantic_analyzer.py`: Vision-based tagging system using Gemini.

---

## 🏁 Getting Started

1.  **Configure Environment**: Copy `.env.template` to `.env` and fill in your Jira credentials and API keys.
2.  **Initialize Sync**: Run `python sync_initial_state.py` to populate your garden with existing project data.
3.  **Launch Middleware**:
    ```bash
    python middleware.py
    ```
4.  **Expose Webhooks**: Use `start_ngrok.ps1` to map Jira webhooks to your local environment.

---

*“Visualizing progress is the first step toward achieving it. BloomPath makes that progress tangible, organic, and beautiful.”*
