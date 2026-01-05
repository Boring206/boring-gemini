"""
Integration tests for MCP Server startup and basic functionality.
"""

import pytest


class TestMCPServerStartup:
    """Test MCP server can start and respond to basic commands."""

    def test_server_module_imports(self):
        """Verify all server modules can be imported without errors."""
        from boring.mcp import server

        assert hasattr(server, "get_server_instance")
        assert hasattr(server, "create_server")

    def test_server_instance_creation(self):
        """Verify server instance can be created."""
        import os

        os.environ["BORING_MCP_MODE"] = "1"

        from boring.mcp import instance

        if not instance.MCP_AVAILABLE:
            pytest.skip("fastmcp not installed")

        from boring.mcp.server import get_server_instance

        try:
            mcp_instance = get_server_instance()
        except RuntimeError as e:
            if "fastmcp" in str(e):
                pytest.skip("fastmcp not found (runtime error)")
            raise e

        assert mcp_instance is not None

        # Verify tools are registered
        # Access through tool manager (FastMCP v2+)
        if hasattr(mcp_instance, "_tool_manager"):
            tool_count = len(mcp_instance._tool_manager._tools)
        else:
            # Fallback for older versions or mocks
            tool_count = len(getattr(mcp_instance, "_tools", []))

        assert tool_count >= 30, f"Expected 30+ tools, got {tool_count}"

    def test_v10_tools_registered(self):
        """Verify V10 tools (RAG, Agents, Shadow) are properly registered."""
        import os

        if os.environ.get("BORING_MCP_MODE") != "1":
            os.environ["BORING_MCP_MODE"] = "1"

        from boring.mcp import instance

        if not instance.MCP_AVAILABLE:
            pytest.skip("fastmcp not installed")

        from boring.mcp.server import get_server_instance

        try:
            mcp_instance = get_server_instance()
        except RuntimeError as e:
            if "fastmcp" in str(e):
                pytest.skip("fastmcp not found (runtime error)")
            raise e

        if hasattr(mcp_instance, "_tool_manager"):
            tool_names = list(mcp_instance._tool_manager._tools.keys())
        else:
            tool_names = list(getattr(mcp_instance, "_tools", {}).keys())

        # V10 RAG tools
        assert "boring_rag_index" in tool_names
        assert "boring_rag_search" in tool_names

        # V10 Agent tools
        assert "boring_multi_agent" in tool_names
        assert "boring_agent_plan" in tool_names

        # V10 Shadow Mode tools
        assert "boring_shadow_status" in tool_names
        assert "boring_shadow_mode" in tool_names


class TestRAGSystem:
    """Test RAG system initialization and basic operations."""

    def test_rag_retriever_creation(self):
        """Test RAGRetriever can be created."""
        import tempfile
        from pathlib import Path

        # ignore_cleanup_errors=True is required on Windows because
        # ChromaDB/SQLite might hold file locks even after object is deleted
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            from boring.rag import create_rag_retriever

            retriever = create_rag_retriever(Path(tmpdir))
            assert retriever is not None

    def test_code_indexer_creation(self):
        """Test CodeIndexer can be created and parses Python."""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def hello(): pass")

            from boring.rag.code_indexer import CodeIndexer

            indexer = CodeIndexer(Path(tmpdir))
            chunks = list(indexer.index_file(test_file))

            assert len(chunks) > 0


class TestShadowMode:
    """Test Shadow Mode guard functionality."""

    def test_shadow_guard_creation(self):
        """Test ShadowModeGuard can be created with default mode."""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            from boring.shadow_mode import ShadowModeLevel, create_shadow_guard

            guard = create_shadow_guard(Path(tmpdir), mode="ENABLED")
            assert guard is not None
            assert guard.mode == ShadowModeLevel.ENABLED

    def test_high_risk_operation_blocked(self):
        """Test that high-risk operations are blocked in ENABLED mode."""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            from boring.shadow_mode import create_shadow_guard

            guard = create_shadow_guard(Path(tmpdir), mode="ENABLED")

            op = {"name": "delete_file", "args": {"file_path": "important.py"}}
            pending = guard.check_operation(op)

            assert pending is not None
            assert "DELETE" in pending.operation_type.upper()


class TestAgentSystem:
    """Test Multi-Agent system components."""

    def test_agent_imports(self):
        """Test all agent classes can be imported."""
        from boring.agents import (
            AgentOrchestrator,
            ArchitectAgent,
        )

        assert ArchitectAgent is not None
        assert AgentOrchestrator is not None

    def test_agent_context_creation(self):
        """Test AgentContext initialization."""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            from boring.agents import AgentContext

            ctx = AgentContext(project_root=Path(tmpdir), task_description="Test task")

            assert ctx.task_description == "Test task"
            assert ctx.project_root == Path(tmpdir)
