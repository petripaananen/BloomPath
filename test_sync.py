import os
from unittest.mock import patch

# Set environment variables for the test before importing middleware
os.environ.setdefault("JIRA_DOMAIN", "petri-paananen.atlassian.net")
os.environ.setdefault("JIRA_PROJECT_KEY", "KAN") 

from middleware import sync_initial_state

# Mock trigger_ue5_growth to avoid connection errors if UE5 is not running
with patch('middleware.trigger_ue5_growth') as mock_trigger:
    mock_trigger.return_value = {"status": "success"}
    sync_initial_state()
    
    print(f"\nMocked UE5 trigger called {mock_trigger.call_count} times.")
    for call in mock_trigger.call_args_list:
        print(f"  - Triggered for: {call.args[0]}")
