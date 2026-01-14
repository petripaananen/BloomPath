# BloomPath Feature Roadmap

Future enhancements for the Digital Twin of Organization.

---

## Phase 3: Environmental Dynamics

### Sprint Weather System
- [ ] Query Jira for sprint burndown data
- [ ] Calculate "on track" vs "behind" metrics
- [ ] Implement UE5 weather state machine (Sunny → Cloudy → Storm)
- [ ] Connect middleware to send weather updates
- [ ] Add Niagara particle effects (rain, sun rays)

### Time-of-Day Mapping
- [ ] Map sprint progress (0-100%) to time of day
- [ ] Dawn = Sprint start, Sunset = Sprint end
- [ ] Dynamic lighting in UE5

---

## Phase 4: Social Layer

### Team Member Avatars
- [ ] Query Jira for issue assignees
- [ ] Create gardener NPC Blueprint
- [ ] Spawn avatar near assigned flower
- [ ] "Planting" animation when task completes
- [ ] Avatar cleanup when reassigned

---

## Phase 5: Audio Feedback

### Ambient Soundscape
- [ ] Growth sound effects (chimes, nature sounds)
- [ ] Birdsong intensity tied to Done issue count
- [ ] Ominous tones for blockers
- [ ] Audio manager Blueprint

---

## Phase 6: Historical Visualization

### Garden Time Machine
- [ ] Store garden state snapshots in database
- [ ] Time slider UI widget
- [ ] Playback animation of growth over time
- [ ] Export to video for presentations

---

## Phase 7: Scale & Multi-Project

### Multi-Project Gardens
- [ ] Query multiple Jira projects
- [ ] Separate garden zones per project
- [ ] Connecting paths between related projects
- [ ] Organization-wide health dashboard

### Sprint Timeline Path
- [ ] Physical path through garden
- [ ] Each sprint = section of path
- [ ] Completed sprints fully grown
- [ ] Current sprint actively growing

---

## Priority Matrix

| Feature | Impact | Effort | Thesis Value |
|---------|--------|--------|--------------|
| Weather System | High | Medium | ⭐⭐⭐ |
| Audio Feedback | Medium | Low | ⭐⭐ |
| Team Avatars | High | High | ⭐⭐⭐ |
| Time Machine | High | High | ⭐⭐⭐ |
| Multi-Project | Medium | High | ⭐⭐ |

---

## Quick Wins (Low Effort, High Polish)

1. **Audio Feedback** - Adds immersion with minimal code
2. **Time-of-Day** - UE5 has built-in support
3. **Weather particles** - Niagara templates available
