"""Tests for boring.agents.bus module."""

import pytest

from boring.agents.bus import AgentBus, AgentMessage, SharedMemory, get_agent_bus


class TestAgentMessage:
    """Tests for AgentMessage dataclass."""

    def test_message_creation(self):
        msg = AgentMessage(sender="agent1", payload="Hello")
        assert msg.sender == "agent1"
        assert msg.payload == "Hello"
        assert msg.topic == "general"
        assert msg.recipient is None
        assert msg.id.startswith("msg_")

    def test_message_with_recipient(self):
        msg = AgentMessage(sender="agent1", recipient="agent2", payload={"key": "value"})
        assert msg.recipient == "agent2"
        assert msg.payload == {"key": "value"}

    def test_message_with_topic(self):
        msg = AgentMessage(sender="agent1", topic="errors", payload="Error occurred")
        assert msg.topic == "errors"


class TestSharedMemory:
    """Tests for SharedMemory class."""

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        memory = SharedMemory()
        await memory.set("key1", "value1")
        result = await memory.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_default(self):
        memory = SharedMemory()
        result = await memory.get("nonexistent", "default_value")
        assert result == "default_value"

    @pytest.mark.asyncio
    async def test_delete(self):
        memory = SharedMemory()
        await memory.set("key1", "value1")
        await memory.delete("key1")
        result = await memory.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_clear(self):
        memory = SharedMemory()
        await memory.set("key1", "value1")
        await memory.set("key2", "value2")
        await memory.clear()
        assert memory.get_all() == {}

    def test_get_all(self):
        memory = SharedMemory()
        memory._storage = {"a": 1, "b": 2}
        result = memory.get_all()
        assert result == {"a": 1, "b": 2}
        # Ensure it's a copy
        result["c"] = 3
        assert "c" not in memory._storage


class TestAgentBus:
    """Tests for AgentBus class."""

    @pytest.mark.asyncio
    async def test_register_agent(self):
        bus = AgentBus()
        await bus.register_agent("test_agent")
        assert "test_agent" in bus.queues

    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self):
        bus = AgentBus()
        received = []

        async def handler(message: AgentMessage):
            received.append(message)

        await bus.subscribe("test_topic", handler)
        msg = AgentMessage(sender="agent1", topic="test_topic", payload="test_payload")
        await bus.publish(msg)

        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_send_direct_message(self):
        bus = AgentBus()
        await bus.register_agent("receiver")

        msg = AgentMessage(sender="sender", recipient="receiver", payload="direct_msg")
        await bus.send_direct(msg)

        # Receive the message
        received = await bus.receive("receiver", timeout=1.0)
        assert received is not None
        assert received.payload == "direct_msg"

    @pytest.mark.asyncio
    async def test_send_direct_to_unregistered(self):
        bus = AgentBus()
        msg = AgentMessage(sender="sender", recipient="unknown", payload="test")
        # Should not raise, just log warning
        await bus.send_direct(msg)

    @pytest.mark.asyncio
    async def test_receive_timeout(self):
        bus = AgentBus()
        await bus.register_agent("agent1")

        # Should timeout and return None
        result = await bus.receive("agent1", timeout=0.1)
        assert result is None

    @pytest.mark.asyncio
    async def test_receive_unregistered(self):
        bus = AgentBus()
        result = await bus.receive("unregistered")
        assert result is None


class TestGetAgentBus:
    """Tests for get_agent_bus singleton."""

    def test_returns_singleton(self):
        # Reset global state
        import boring.agents.bus as bus_module

        bus_module._global_bus = None

        bus1 = get_agent_bus()
        bus2 = get_agent_bus()
        assert bus1 is bus2

    def test_creates_instance(self):
        import boring.agents.bus as bus_module

        bus_module._global_bus = None

        bus = get_agent_bus()
        assert isinstance(bus, AgentBus)
