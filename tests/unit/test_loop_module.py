"""
Tests for loop module (agent loop components).
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestLoopImports:
    """Tests for loop module imports."""

    def test_loop_module_imports(self):
        """Test that loop module can be imported."""
        from boring import loop
        
        assert loop is not None

    def test_agent_imports(self):
        """Test that agent module imports."""
        from boring.loop import agent
        
        assert agent is not None

    def test_base_imports(self):
        """Test that base module imports."""
        from boring.loop import base
        
        assert base is not None

    def test_context_imports(self):
        """Test that context module imports."""
        from boring.loop import context
        
        assert context is not None


class TestLoopContext:
    """Tests for LoopContext."""

    def test_loop_context_creation(self, tmp_path):
        """Test creating a loop context with defaults."""
        from boring.loop.context import LoopContext
        
        ctx = LoopContext(project_root=tmp_path)
        
        assert ctx.project_root == tmp_path

    def test_loop_context_has_loop_count(self, tmp_path):
        """Test loop context has loop_count."""
        from boring.loop.context import LoopContext
        
        ctx = LoopContext(project_root=tmp_path)
        
        assert hasattr(ctx, 'loop_count')
        assert ctx.loop_count == 0

    def test_loop_context_has_max_loops(self, tmp_path):
        """Test loop context has max_loops."""
        from boring.loop.context import LoopContext
        
        ctx = LoopContext(project_root=tmp_path)
        
        assert hasattr(ctx, 'max_loops')
        assert ctx.max_loops > 0

    def test_loop_context_start_loop(self, tmp_path):
        """Test start_loop method."""
        from boring.loop.context import LoopContext
        
        ctx = LoopContext(project_root=tmp_path)
        ctx.start_loop()
        
        assert ctx.loop_start_time > 0

    def test_loop_context_increment_loop(self, tmp_path):
        """Test increment_loop method."""
        from boring.loop.context import LoopContext
        
        ctx = LoopContext(project_root=tmp_path)
        assert ctx.loop_count == 0
        
        ctx.increment_loop()
        
        assert ctx.loop_count == 1

    def test_loop_context_should_continue(self, tmp_path):
        """Test should_continue method."""
        from boring.loop.context import LoopContext
        
        ctx = LoopContext(project_root=tmp_path)
        
        assert ctx.should_continue() is True

    def test_loop_context_mark_exit(self, tmp_path):
        """Test mark_exit method."""
        from boring.loop.context import LoopContext
        
        ctx = LoopContext(project_root=tmp_path)
        ctx.mark_exit("Test reason")
        
        assert ctx.should_exit is True
        assert ctx.exit_reason == "Test reason"


class TestBaseLoop:
    """Tests for base loop class."""

    def test_base_loop_exists(self):
        """Test that base module has expected content."""
        from boring.loop import base
        
        # Check for StateResult enum and LoopState class
        assert hasattr(base, 'StateResult')
        assert hasattr(base, 'LoopState')


class TestAgentLoop:
    """Tests for agent loop."""

    def test_agent_loop_import(self):
        """Test agent loop can be imported."""
        from boring.loop.agent import StatefulAgentLoop
        
        assert StatefulAgentLoop is not None
