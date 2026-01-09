# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Unit tests for Agent Protocol.
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from boring.agents.agent_protocol import (
    AgentProtocol, 
    AgentRole, 
    MessageType, 
    AgentHandoff,
    get_agent_protocol,
    _agent_protocol
)

@pytest.fixture
def protocol():
    with TemporaryDirectory() as tmp_dir:
        # Reset singleton for testing
        import boring.agents.agent_protocol as ap
        ap._agent_protocol = None
        yield get_agent_protocol(Path(tmp_dir))

def test_protocol_initialization(protocol):
    assert protocol.project_root is not None
    assert protocol.data_dir.exists()
    assert protocol._message_queue == []

def test_send_message(protocol):
    msg_id = protocol.send_message(
        sender=AgentRole.ARCHITECT,
        recipient=AgentRole.CODER,
        message_type=MessageType.REQUEST,
        content={"task": "implement feature"}
    )
    assert msg_id is not None
    assert len(protocol._message_queue) == 1
    assert protocol._message_queue[0].sender == AgentRole.ARCHITECT

def test_get_messages(protocol):
    protocol.send_message(AgentRole.ARCHITECT, AgentRole.CODER, MessageType.REQUEST, {"id": 1})
    protocol.send_message(AgentRole.CODER, AgentRole.REVIEWER, MessageType.REQUEST, {"id": 2})
    
    coder_msgs = protocol.get_messages(AgentRole.CODER)
    assert len(coder_msgs) == 1
    assert coder_msgs[0].content["id"] == 1

def test_respond_to_message(protocol):
    msg_id = protocol.send_message(AgentRole.ARCHITECT, AgentRole.CODER, MessageType.REQUEST, {"q": "?"})
    resp_id = protocol.respond_to_message(msg_id, AgentRole.CODER, {"a": "!"})
    
    assert resp_id != ""
    msgs = protocol.get_messages(AgentRole.ARCHITECT)
    assert any(m.response_to == msg_id for m in msgs)

def test_shared_context(protocol):
    ctx = protocol.create_shared_context("task-123", "Test Task")
    assert ctx.task_id == "task-123"
    assert ctx.current_phase == "planning"
    
    protocol.update_context(AgentRole.ARCHITECT, {"phase": "coding", "note": "started"})
    updated_ctx = protocol.get_shared_context()
    assert updated_ctx.current_phase == "coding"
    assert "architect" in updated_ctx.agent_notes

def test_consensus_voting(protocol):
    vote_id = protocol.start_vote("Should we release?", ["yes", "no"], [AgentRole.CODER, AgentRole.REVIEWER])
    assert vote_id is not None
    
    protocol.cast_vote(vote_id, AgentRole.CODER, "yes")
    protocol.cast_vote(vote_id, AgentRole.REVIEWER, "yes")
    
    result = protocol.get_vote_result(vote_id)
    assert result.winner == "yes"
    assert result.consensus_reached is True

def test_performance_tracking(protocol):
    protocol.record_task_completion(AgentRole.CODER, success=True, response_time_ms=100.0)
    perf = protocol.get_agent_performance(AgentRole.CODER)
    assert perf.tasks_completed == 1
    assert perf.success_rate == 1.0

def test_agent_handoff():
    msg = AgentHandoff.architect_to_coder({"plan": "abc"}, ["file1.py"])
    assert msg.message_type == MessageType.HANDOFF
    assert msg.sender == AgentRole.ARCHITECT
    assert msg.recipient == AgentRole.CODER
