"""
Tests for WFM-3: Command Batching Optimization.
"""
import pytest
from ue5_interface import CommandBatcher, BATCHER, trigger_ue5_sync_all_vines
from unittest.mock import MagicMock, patch

def test_command_batcher_logic():
    batcher = CommandBatcher()
    batcher.add("print('cmd1')")
    batcher.add("print('cmd2')")
    
    # Verify buffer contents
    assert len(batcher._buffer) == 2
    assert batcher._buffer[0] == "print('cmd1')"
    
    # Mock AGENT execution
    with patch("ue5_interface.AGENT") as mock_agent:
        mock_agent.execute_python.return_value = "done"
        
        result = batcher.flush()
        
        # Verify execution call
        mock_agent.execute_python.assert_called_once()
        call_arg = mock_agent.execute_python.call_args[0][0]
        assert "print('cmd1')\nprint('cmd2')" in call_arg
        
        # Verify buffer clear
        assert len(batcher._buffer) == 0
        assert result["output"] == "done"

def test_batch_vines_function():
    BATCHER.clear() # Ensure clean state
    
    deps = [
        {"from": "A", "to": "B", "type": "blocked_by"},
        {"from": "A", "to": "C", "type": "relates_to"}
    ]
    
    with patch("ue5_interface.AGENT") as mock_agent:
        mock_agent.execute_python.return_value = "batch_done"
        
        trigger_ue5_sync_all_vines(deps)
        
        # Should result in ONE execution call
        assert mock_agent.execute_python.call_count == 1
        
        script = mock_agent.execute_python.call_args[0][0]
        
        # Check that it contains calls for both vines
        assert "Spawn_Dependency_Vine" in script
        assert "A" in script and "B" in script  # vine 1
        assert "A" in script and "C" in script  # vine 2
