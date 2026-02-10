---
description: How to create and manage Linear tasks for the Garden Protocol project
---

# Linear Task Management Workflow

All tasks for BloomPath live in the **Garden Protocol** project under the **World Foundational Models** team in Linear.

## 1. Create Task → Backlog

Create every new task in the **Backlog** column:

```
Tool: mcp_linear-mcp-server_create_issue
  team: "World Foundational Models"
  project: "Garden Protocol"
  state: "Backlog"
  title: "<descriptive title>"
  description: "<markdown description with acceptance criteria>"
  priority: 1=Urgent, 2=High, 3=Normal, 4=Low
```

### Labels (apply as needed)
| Label | When to use |
|-------|-------------|
| **World Lab** | Task involves World Labs API (3D generation) |
| **Feature** | New functionality |
| **Improvement** | Enhancement to existing functionality |
| **Bug** | Defect or broken behavior |

### Dependencies
If the new task **depends on** another task, set `blockedBy`. If it **blocks** another task, set `blocks`. Use logic:
- A task that modifies shared modules (e.g. `core.py`, `orchestrator.py`) **blocks** tasks that consume those modules.
- A task requiring API output from another service **is blocked by** the integration task for that service.
- Create dependencies automatically when the relationship is obvious from the task descriptions.

```
Tool: mcp_linear-mcp-server_update_issue
  id: "<new issue ID>"
  blockedBy: ["WFM-XX"]   # issues this depends on
  blocks: ["WFM-YY"]      # issues this blocks
```

## 2. Backlog → Todo

- **Urgent/High priority** tasks: Move to **Todo** immediately after creation.
- **Normal/Low priority** tasks: Stay in Backlog. Move to Todo on a case-by-case basis when ready to work on them.

```
Tool: mcp_linear-mcp-server_update_issue
  id: "WFM-XX"
  state: "Todo"
```

## 3. Todo → In Progress

When starting work on a task:

```
Tool: mcp_linear-mcp-server_update_issue
  id: "WFM-XX"
  state: "In Progress"
```

## 4. In Progress → In Review

When implementation is complete but not yet tested:

```
Tool: mcp_linear-mcp-server_update_issue
  id: "WFM-XX"
  state: "In Review"
```

## 5. In Review → Done

Once all test cases pass:

```
Tool: mcp_linear-mcp-server_update_issue
  id: "WFM-XX"
  state: "Done"
```

## Quick Reference

```
Backlog → Todo → In Progress → In Review → Done
```

**Linear project**: Garden Protocol  
**Linear team**: World Foundational Models  
**Available statuses**: Backlog, Todo, In Progress, In Review, Done, Canceled, Duplicate
