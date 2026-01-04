
import pytest
from unittest.mock import MagicMock, patch, ANY
import sys

# Mock imports for modules not yet loaded or to control behavior
# We need to ensure boring.mcp.tools.agents can import boring.memory
# But we want to mock MemoryManager class

def test_boring_delegate_telemetry():
    """Test that boring_delegate records metrics."""
    # We need to patch where it is imported inside the function, 
    # OR since it's a lazy import, we can patch sys.modules or use patch specifically on the module path.
    # The function imports: form ...memory import MemoryManager
    
    with patch("boring.memory.MemoryManager") as MockMemoryCls, \
         patch("boring.mcp.tools.agents.get_project_root_or_error") as mock_get_root:
        
        # Setup mocks
        mock_get_root.return_value = (MagicMock(), None)
        mock_memory_instance = MockMemoryCls.return_value
        
        from boring.mcp.tools.agents import boring_delegate
        
        # Call tool
        task = "Analyze database"
        tool_type = "database"
        result = boring_delegate(task=task, tool_type=tool_type)
        
        # Verify result is a template
        assert result["status"] == "WORKFLOW_TEMPLATE"
        assert result["workflow"] == "delegate"
        
        # Verify telemetry was called
        MockMemoryCls.assert_called_once()
        mock_memory_instance.record_metric.assert_called_once_with(
            "delegate_usage", 
            1.0, 
            {"task": task, "tool_type": tool_type}
        )

def test_boring_delegate_telemetry_failure_silence():
    """Test that telemetry failure doesn't break the tool."""
    with patch("boring.memory.MemoryManager") as MockMemoryCls, \
         patch("boring.mcp.tools.agents.get_project_root_or_error") as mock_get_root:
        
        mock_get_root.return_value = (MagicMock(), None)
        # Simulate crash in memory init or record
        MockMemoryCls.side_effect = Exception("DB Connection Failed")
        
        from boring.mcp.tools.agents import boring_delegate
        
        # Should not raise exception
        result = boring_delegate("Task", "api")
        
        assert result["status"] == "WORKFLOW_TEMPLATE"

def test_boring_delegate_cot():
    """Test that delegate prompts include Chain-of-Thought."""
    with patch("boring.mcp.tools.agents.get_project_root_or_error") as mock_get_root:
        mock_get_root.return_value = (MagicMock(), None)
        # Patch memory to avoid import error if mocked above fails context
        with patch("boring.memory.MemoryManager"):
            from boring.mcp.tools.agents import boring_delegate
            
            # Test DB
            res_db = boring_delegate("Task", "database")
            assert "Thinking Process" in res_db["routing_info"]["prompt"]
            
            # Test Active Reasoning
            res_reason = boring_delegate("Task", "reasoning")
            assert "Thinking Process" in res_reason["routing_info"]["prompt"]
