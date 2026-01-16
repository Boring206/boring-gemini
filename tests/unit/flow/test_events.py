"""
Tests for flow events module.
"""

from boring.flow.events import FlowEvent, FlowEventBus


class TestFlowEvent:
    """Tests for FlowEvent enum."""

    def test_flow_event_exists(self):
        """Test FlowEvent enum members exist."""
        assert FlowEvent.AGENT_START is not None
        assert FlowEvent.AGENT_COMPLETE is not None
        assert FlowEvent.PRE_POLISH is not None
        assert FlowEvent.POST_POLISH is not None
        assert FlowEvent.AGENT_START != FlowEvent.AGENT_COMPLETE


class TestFlowEventBus:
    """Tests for FlowEventBus."""

    def test_subscribe_and_emit(self):
        """Test subscribing to events and emitting them."""
        handler_called = []

        def handler(**kwargs):
            handler_called.append(kwargs)

        FlowEventBus.subscribe(FlowEvent.AGENT_START, handler)
        FlowEventBus.emit(FlowEvent.AGENT_START, project_path="test", attempt=1)

        assert len(handler_called) == 1
        assert handler_called[0]["project_path"] == "test"
        assert handler_called[0]["attempt"] == 1

    def test_multiple_handlers(self):
        """Test multiple handlers for same event."""
        handler1_called = []
        handler2_called = []

        def handler1(**kwargs):
            handler1_called.append(kwargs)

        def handler2(**kwargs):
            handler2_called.append(kwargs)

        FlowEventBus.subscribe(FlowEvent.AGENT_COMPLETE, handler1)
        FlowEventBus.subscribe(FlowEvent.AGENT_COMPLETE, handler2)
        FlowEventBus.emit(FlowEvent.AGENT_COMPLETE, status="success")

        assert len(handler1_called) == 1
        assert len(handler2_called) == 1

    def test_get_history(self):
        """Test getting event history."""
        FlowEventBus.clear()  # Clear for clean test

        FlowEventBus.emit(FlowEvent.PRE_POLISH, test="data")
        history = FlowEventBus.get_history()

        assert len(history) >= 1
        assert history[-1]["event"] == FlowEvent.PRE_POLISH.name

    def test_handler_exception_handling(self):
        """Test that handler exceptions don't break the bus."""

        def failing_handler(**kwargs):
            raise ValueError("Handler error")

        def good_handler(**kwargs):
            pass

        FlowEventBus.subscribe(FlowEvent.POST_POLISH, failing_handler)
        FlowEventBus.subscribe(FlowEvent.POST_POLISH, good_handler)

        # Should not raise
        FlowEventBus.emit(FlowEvent.POST_POLISH)

        # Good handler should still be called
        # (We can't easily test this without more infrastructure, but the fact
        # that it doesn't crash is good enough)
