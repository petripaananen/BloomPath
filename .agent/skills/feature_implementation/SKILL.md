---
name: Feature Implementation
description: Standardized workflow for planning, building, and verifying new features using the Agentic Mode artifacts.
---

# Feature Implementation Skill

Use this skill whenever the user asks for a feature that requires planning, coding, and verification.

## 1. Task Initialization
- [ ] Open `task.md`.
- [ ] Add the new feature as a top-level item with an empty checkbox `[ ]`.
- [ ] Add sub-tasks for Planning, Implementation, and Verification.

## 2. Planning Phase
- [ ] Create or update `implementation_plan.md`.
- [ ] Structure the plan:
    - **Goal**: One sentence summary.
    - **Proposed Changes**: File-by-file breakdown.
    - **Verification Plan**: How to test (Unit tests, Manual steps).
- [ ] **CRITICAL**: Use `notify_user` to request approval before writing code.

## 3. Implementation Phase
- [ ] Once approved, mark Planning as completed in `task.md`.
- [ ] Create/Edit files as per the plan.
- [ ] Adhere to project architecture (e.g., use `IssueProvider` for management tools, `ue5_interface` for Unreal).

## 4. Verification Phase
- [ ] Run existing tests to ensure no regressions.
- [ ] Create new tests for the feature if applicable.
- [ ] Create/Update `walkthrough.md` to document the change.
    - Include "What was changed" and "How to verify".
- [ ] **Git Operations**:
    - `git add <files>`
    - `git commit -m "feat: <description>"`
    - `git push`

## 5. Completion
- [ ] Mark the feature as `[x]` in `task.md`.
- [ ] Notify user of completion.
