"""
Unit tests for Multi-Agent system
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch


class TestAgentBase:
    """Tests for base agent types"""
    
    def test_agent_role_enum(self):
        """Test AgentRole enum"""
        from boring.agents.base import AgentRole
        
        assert AgentRole.ARCHITECT.value == "architect"
        assert AgentRole.CODER.value == "coder"
        assert AgentRole.REVIEWER.value == "reviewer"
    
    def test_shared_resource(self):
        """Test SharedResource dataclass"""
        from boring.agents.base import SharedResource, AgentRole
        
        resource = SharedResource(
            name="test_resource",
            content={"key": "value"},
            version=1,
            last_updated_by=AgentRole.ARCHITECT
        )
        
        assert resource.name == "test_resource"
        assert resource.content["key"] == "value"
        
        # Test serialization
        data = resource.to_dict()
        assert data["version"] == 1
        assert data["last_updated_by"] == "architect"
    
    def test_agent_message(self):
        """Test AgentMessage dataclass"""
        from boring.agents.base import AgentMessage, AgentRole
        
        msg = AgentMessage(
            sender=AgentRole.ARCHITECT,
            receiver=AgentRole.CODER,
            action="plan_created",
            summary="Created plan",
            requires_approval=True,
            approval_reason="Human review needed"
        )
        
        assert msg.sender == AgentRole.ARCHITECT
        assert msg.requires_approval is True
    
    def test_agent_context(self, tmp_path):
        """Test AgentContext"""
        from boring.agents.base import AgentContext, AgentRole
        
        context = AgentContext(
            project_root=tmp_path,
            task_description="Build feature X"
        )
        
        # Test resource management
        context.set_resource("plan", "My plan", AgentRole.ARCHITECT)
        
        assert context.get_resource("plan") == "My plan"
        assert context.resources["plan"].version == 1
        
        # Update resource
        context.set_resource("plan", "Updated plan", AgentRole.ARCHITECT)
        assert context.resources["plan"].version == 2


class TestArchitectAgent:
    """Tests for ArchitectAgent"""
    
    def test_architect_system_prompt(self):
        """Test Architect has correct system prompt"""
        from boring.agents.architect import ArchitectAgent
        
        mock_client = Mock()
        architect = ArchitectAgent(mock_client)
        
        prompt = architect.system_prompt
        assert "ARCHITECT" in prompt
        assert "PLAN" in prompt
        assert "NEVER write actual code" in prompt.upper() or "NEVER writes code" in prompt.upper() or "NEVER" in prompt
    
    def test_extract_file_list(self):
        """Test file extraction from plan"""
        from boring.agents.architect import ArchitectAgent
        
        mock_client = Mock()
        architect = ArchitectAgent(mock_client)
        
        plan = """
        ### Files to Modify
        - `src/main.py`: Main entry point
        - `tests/test_main.py`: [NEW] Unit tests
        """
        
        files = architect._extract_file_list(plan)
        assert "src/main.py" in files
        assert "tests/test_main.py" in files


class TestReviewerAgent:
    """Tests for ReviewerAgent"""
    
    def test_reviewer_system_prompt(self):
        """Test Reviewer has correct system prompt"""
        from boring.agents.reviewer import ReviewerAgent
        
        mock_client = Mock()
        reviewer = ReviewerAgent(mock_client)
        
        prompt = reviewer.system_prompt
        assert "REVIEWER" in prompt or "Devil" in prompt
        assert "BUG" in prompt.upper() or "PROBLEMS" in prompt.upper()
    
    def test_extract_verdict_pass(self):
        """Test verdict extraction for PASS"""
        from boring.agents.reviewer import ReviewerAgent
        
        mock_client = Mock()
        reviewer = ReviewerAgent(mock_client)
        
        review = """
        ### Review Summary
        **Verdict:** PASS
        
        All looks good!
        """
        
        verdict = reviewer._extract_verdict(review)
        assert verdict == "PASS"
    
    def test_extract_verdict_needs_work(self):
        """Test verdict extraction for NEEDS_WORK"""
        from boring.agents.reviewer import ReviewerAgent
        
        mock_client = Mock()
        reviewer = ReviewerAgent(mock_client)
        
        review = """
        **Verdict:** NEEDS_WORK
        
        - [🔴 CRITICAL] Missing error handling in login()
        """
        
        verdict = reviewer._extract_verdict(review)
        assert verdict == "NEEDS_WORK"
    
    def test_extract_issues(self):
        """Test issue extraction"""
        from boring.agents.reviewer import ReviewerAgent
        
        mock_client = Mock()
        reviewer = ReviewerAgent(mock_client)
        
        review = """
        ### Issues Found
        - [🔴 CRITICAL] SQL injection vulnerability
        - [🟠 MAJOR] Missing input validation
        - [🟡 MINOR] Typo in docstring
        """
        
        issues = reviewer._extract_issues(review)
        assert len(issues["critical"]) == 1
        assert "SQL injection" in issues["critical"][0]
        assert len(issues["major"]) == 1
        assert len(issues["minor"]) == 1


class TestOrchestratorInit:
    """Tests for AgentOrchestrator initialization"""
    
    def test_orchestrator_creates_agents(self, tmp_path):
        """Test orchestrator creates all agents"""
        from boring.agents.orchestrator import AgentOrchestrator
        from boring.agents.base import AgentRole
        
        mock_client = Mock()
        
        orchestrator = AgentOrchestrator(
            llm_client=mock_client,
            project_root=tmp_path
        )
        
        assert orchestrator.architect is not None
        assert orchestrator.coder is not None
        assert orchestrator.reviewer is not None
        assert orchestrator._agents[AgentRole.ARCHITECT] is not None
