---
description: Generate high-resolution technical diagrams for BloomPath architecture using PaperVizAgent
---
1.  **Extract Pipeline Structure**:
    - Identify current middleware/UE5 endpoints and updated integration logic.
2.  **Generate Architecture Description**:
    - Draft a natural language markdown description of the architecture in `tmp_arch.md`.
    - Be detailed about the data sources, middleware functions, and AI loop (Linear/Jira -> Receiver -> Orchestrator -> Marble/Gemini/PaperViz -> UE5).
3.  **Set Environment Keys**:
    - Ensure your `GOOGLE_API_KEY` is exported or configured in `tools/papervizagent/configs/model_config.yaml`.
// turbo
4.  **Run PaperVizAgent Development Render**:
    - Change directory to `tools/papervizagent/`.
    - Activate the virutal environment: `.\.venv\Scripts\activate`.
    - Execute: `python generate_bloompath.py ../../tmp_arch.md ../../docs/BloomPath_Architecture_Latest.png`.
5.  **Review Visual Quality**:
    - The diagram is automatically refined via the built-in Planner -> Visualizer -> Critic loop. 
    - Review `docs/BloomPath_Architecture_Latest.png`.
6.  **Finalize Documentation & Commit**:
    - Update `README.md` to reflect new architecture concepts.
    - Delete `tmp_arch.md`.
    - Commit `README.md` and the `docs/*.png` assets.
