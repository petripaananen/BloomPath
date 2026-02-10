---
description: How to generate a new 3D world from a Linear issue using the PWM pipeline
---

# Generate a New 3D World

## Steps

1. Create a Linear issue with the **World Lab** label:
```
Tool: mcp_linear-mcp-server_create_issue
  team: "World Foundational Models"
  project: "Garden Protocol"
  state: "Backlog"
  labels: ["World Lab"]
  title: "<scene description>"
  description: "<detailed prompt with objects, lighting, style, atmosphere>"
  priority: <1-4>
```

2. Move the issue to **Todo** to trigger the automatic PWM pipeline:
```
Tool: mcp_linear-mcp-server_update_issue
  id: "WFM-XX"
  state: "Todo"
```

3. Monitor the orchestrator logs for generation progress:
```powershell
cd c:\Users\petri\.gemini\antigravity\BloomPath
Get-Content middleware.log -Tail 30 -Wait
```

4. Verify output files were created:
```powershell
ls c:\Users\petri\.gemini\antigravity\BloomPath\content\generated\
```

5. If verified in UE5, move to Done:
```
Tool: mcp_linear-mcp-server_update_issue
  id: "WFM-XX"
  state: "Done"
```

## Prompt Tips
- Be specific about lighting ("warm ambient from fireplace", "soft daylight")
- Name materials and textures ("light oak wood flooring", "gray fabric sofa")
- Describe spatial layout ("fireplace on the back wall", "window on the left")
- Minimum ~20 words for good results
