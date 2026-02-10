---
name: Provider Integration
description: Standardized workflow for adding or modifying Jira/Linear provider integrations in BloomPath.
---

# Provider Integration Skill

Use this skill when adding a new project management provider or modifying existing Jira/Linear integrations.

## Architecture

All providers extend `IssueProvider` (base class in `middleware/providers/base.py`) and normalize data to `UnifiedTicket` (in `middleware/models/ticket.py`).

## 1. Base Class Contract

Every provider must implement these methods:

```python
class NewProvider(IssueProvider):
    @property
    def name(self) -> str: ...

    def parse_webhook(self, data: dict) -> UnifiedTicket: ...
    def get_active_sprint_or_cycle(self) -> Optional[dict]: ...
    def get_sprint_issues(self, sprint_id: str) -> List[UnifiedTicket]: ...
    def get_issue_dependencies(self, issue_id: str) -> list: ...
    def transition_to_done(self, issue_id: str) -> bool: ...
```

## 2. Provider Implementation

- [ ] Create `middleware/providers/<name>.py`.
- [ ] Load credentials from environment variables (`.env`).
- [ ] Implement `parse_webhook()` to normalize to `UnifiedTicket`:
  - Map provider statuses → `IssueStatus` enum (`OPEN`, `IN_PROGRESS`, `DONE`, `BLOCKED`).
  - Map issue types → `IssueType` enum (`BUG`, `TASK`, `STORY`, `EPIC`).
  - Populate: `id`, `title`, `status`, `issue_type`, `priority`, `assignee_*`, `labels`, `provider`.
- [ ] Implement webhook signature verification if the provider supports it.

## 3. Webhook Route

- [ ] Add a new route in `middleware/routes/webhooks.py`:
  ```python
  @webhooks_bp.route('/<provider_name>', methods=['POST'])
  def new_provider_webhook():
      # Parse → detect event → enqueue (use task_queue!)
  ```
- [ ] Create `_detect_<provider>_event(data)` helper for event classification.
- [ ] **CRITICAL**: Use `enqueue_ticket_event()` — never call `process_ticket_event()` synchronously.

## 4. API Routes

- [ ] Update `_get_provider()` in `middleware/routes/api.py` to recognize the new provider.
- [ ] Ensure `/sprint_status`, `/team_members`, `/complete_task` work with the new provider.

## 5. Configuration

- [ ] Add required env vars to `.env.template`.
- [ ] Update `api.py` health check to report the new provider's configuration status.

## 6. Verification

- [ ] Create `test_<provider>.py` with mock webhook payloads.
- [ ] Test the webhook response time (must be < 500ms).
- [ ] Verify `UnifiedTicket` normalization is correct.
