# Diagram Generation Skill

Standardized workflow for generating high-quality architectural illustrations for BloomPath. This skill leverages a multi-agent pipeline inspired by **PaperVizAgent** to ensure technical accuracy and visual clarity.

## Overview
BloomPath diagrams must reflect the real-time state of the middleware and Unreal Engine integration. This skill avoids hallucinated "filler" arrows by using a **Critic-Visualizer loop**.

### Key Agents
1.  **Visualizer Agent**: Translates the Mermaid DSL/Python code into high-resolution PNGs using the `mermaid-cli`.
2.  **Critic Agent**: Uses Gemini Vision to inspect exported images for typical visual bugs (overlapping text, cropped titles, or dense spaghetti-line routing).
3.  **Refinement Agent**: Adjusts the Mermaid source code by injecting node-spacing (`--->` or `&nbsp;`) or subgraph directions based on Critic feedback.

## Standards
- **Resolution**: Minimum 4x scale factor for all PNG exports (`-s 4`).
- **Transparency**: All diagrams must use transparent backgrounds (`-b transparent`).
- **Styling**: Adhere to the `docs/templates/diagram_style.yaml` configuration.
- **Accessibility**: No color-only information. Use distinct arrow types (solid for sync, dashed for async) and icons.

## Workflow Integration
- Use the `middleware/diagram_agent.py` script to generate visuals.
- Always commit both the `.mmd` source and the `.png` result to the `docs/` folder to maintain git-tracked versioning of architectural changes.
- Ensure the `README.md` is updated synchronously with any new diagram generation.

## Troubleshooting
- **Overlapping nodes?** Force the layout by changing the subgraph `direction` (TB/LR) or using invisible links (`A ~~~ B`).
- **Clipped text?** Inject non-breaking spaces (`&nbsp;`) into the subgraph titles to manually expand the container bounding boxes.
- **Spaghetti lines?** Shorten long arrow text labels to give the auto-router more whitespace.
