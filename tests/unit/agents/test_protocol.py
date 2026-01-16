from boring.agents.protocol import AgentResponse, ChatMessage, FunctionCall, ToolCall


def test_chat_message_creation():
    msg = ChatMessage(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"
    assert "timestamp" in msg.model_dump()


def test_tool_call_message():
    tc = ToolCall(function=FunctionCall(name="get_weather", arguments='{"city": "Tokyo"}'))
    msg = ChatMessage(role="assistant", tool_calls=[tc])
    assert msg.role == "assistant"
    assert msg.tool_calls[0].function.name == "get_weather"


def test_serialization():
    tc = ToolCall(function=FunctionCall(name="test", arguments="{}"))
    msg = ChatMessage(role="assistant", tool_calls=[tc])
    json_output = msg.model_dump_json()
    assert "tool_calls" in json_output
    assert "function" in json_output


def test_agent_response():
    msgs = [ChatMessage(role="user", content="Hi"), ChatMessage(role="assistant", content="Yo")]
    resp = AgentResponse(
        messages=msgs, finish_reason="stop", usage={"total_tokens": 10}, latency_ms=150.5
    )
    assert len(resp.messages) == 2
    assert resp.latency_ms == 150.5
