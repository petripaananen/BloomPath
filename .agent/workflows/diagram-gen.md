---
description: Generate high-resolution technical diagrams for BloomPath architecture
---
1.  **Extract Pipeline Structure**:
    - Identify current middleware/UE5 endpoints.
    - Check for updated Jira/Linear integration logic.
2.  **Generate Mermaid DSL**:
    - Draft the technical diagram code in a temporary `diagram.mmd` file.
    - Reference the `diagram_generation` skill for styling rules.
// turbo
3.  **Run Development Render**:
    - Execute: `python middleware/diagram_agent.py diagram.mmd docs/BloomPath_Architecture_Latest.png`.
4.  **Review Visual Quality**:
    - Run the **Critic Agent** script to check for overlaps via `DiagramAgent.analyze_layout()`.
    - If overlaps are detected, manually or programmatically adjust the spacing logic.
5.  **Finalize Documentation**:
    - Copy the generated Mermaid code into `README.md`.
    - Update the documentation's PNG links.
    - Delete the temporary `.mmd` and intermediate generation files.
6.  **Commit with Versioning**:
    - Commit `README.md` and the `docs/*.png` assets.
    - Update the `middleware/__init__.py` version if the architecture significantly changed.
