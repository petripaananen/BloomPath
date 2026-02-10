---
name: World Generation Pipeline
description: Standardized workflow for generating 3D worlds from Linear issues using the PWM pipeline (World Labs → Gemini → UE5).
---

# World Generation Pipeline Skill

Use this skill when creating new 3D environments triggered by Linear issues with the "World Lab" label.

## Pipeline Overview

```
Issue → parse_intent() → World Labs API → Gemini Vision → UE5 Load Level
```

## 1. Issue Setup

- [ ] Ensure the Linear issue has the **World Lab** label.
- [ ] The issue description should contain a **detailed scene prompt** (objects, lighting, style).
- [ ] Move the issue to **Todo** to trigger the automatic pipeline, or run manually.

## 2. Intent Parsing (`orchestrator.py`)

- [ ] `BloomPathOrchestrator.parse_intent(issue)` extracts:
  - `prompt`: The scene description from the issue title + description.
  - `mechanics`: Loaded from `config/mechanics.json` based on issue labels.
- [ ] Verify the prompt is descriptive enough for World Labs (min ~20 words).

## 3. World Generation (`world_client.py`)

- [ ] `WorldLabsClient.generate_world(prompt)` calls the World Labs API.
- [ ] Expected output:
  - `.gltf` mesh saved to `content/generated/<issue_id>_<timestamp>_mesh.gltf`
  - Preview image saved alongside.
- [ ] If generation fails, check:
  - `WORLD_LABS_API_KEY` is set in `.env`
  - API quota is not exceeded
  - Prompt doesn't contain blocked content

## 4. Semantic Analysis (`semantic_analyzer.py`)

- [ ] `semantic_analyzer.analyze_world(image_path)` uses Gemini Vision.
- [ ] Returns a manifest JSON with:
  ```json
  {
    "objects": [
      {"name": "Tree", "semantic_type": "StaticMesh", "tags": ["Nature", "Tall"]}
    ]
  }
  ```
- [ ] Manifest is saved to `content/generated/<issue_id>_<timestamp>_manifest.json`.
- [ ] Verify `GEMINI_API_KEY` is set in `.env`.

## 5. UE5 Injection (`ue5_interface.py`)

- [ ] `trigger_ue5_load_level(mesh_path)` loads the `.gltf` via glTFRuntime.
- [ ] `trigger_ue5_set_tag(object, tag)` applies semantic tags from the manifest.
- [ ] UE5 must be running with the Remote Control API plugin enabled.

## 6. Verification

- [ ] Check `content/generated/` for the mesh and manifest files.
- [ ] Verify UE5 loaded the level (check logs or visual inspection).
- [ ] Run `python test_world_gen.py` for automated checks.
