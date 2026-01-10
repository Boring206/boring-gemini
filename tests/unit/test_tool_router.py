# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

from boring.mcp.tool_router import get_tool_router


def test_router_checkpoint_restore():
    """Verify that natural language for restore is correctly routed."""
    router = get_tool_router()

    # Chinese test
    result = router.route("幫我還原到 Pre-Refactor")
    assert result.matched_tool == "boring_checkpoint"
    assert result.suggested_params["action"] == "restore"
    assert result.suggested_params["name"] == "Pre-Refactor"

    # English test
    result = router.route("rollback to V1.0")
    assert result.matched_tool == "boring_checkpoint"
    assert result.suggested_params["action"] == "restore"
    assert result.suggested_params["name"] == "V1.0"


def test_router_checkpoint_create():
    """Verify that natural language for create is correctly routed."""
    router = get_tool_router()

    # Chinese test
    result = router.route("幫我建立一個存檔叫做 test-point")
    assert result.matched_tool == "boring_checkpoint"
    assert result.suggested_params["action"] == "create"
    assert result.suggested_params["name"] == "test-point"

    # English test
    result = router.route("save current state as checkpoint-alpha")
    assert result.matched_tool == "boring_checkpoint"
    assert result.suggested_params["action"] == "create"
    assert result.suggested_params["name"] == "checkpoint-alpha"


def test_router_checkpoint_list():
    """Verify that natural language for listing checkpoints is correctly routed."""
    router = get_tool_router()

    # Chinese test
    result = router.route("查看所有存檔清單")
    assert result.matched_tool == "boring_checkpoint"
    assert result.suggested_params["action"] == "list"

    # English test
    result = router.route("show me all checkpoints")
    assert result.matched_tool == "boring_checkpoint"
    assert result.suggested_params["action"] == "list"


def test_router_checkpoint_missing_name():
    """Verify that missing name results in a note but correct action."""
    router = get_tool_router()

    result = router.route("還原到某個地方")
    # In this case, "到" might not be followed by a name if the regex is strict
    # "到" is in the regex, if there is no match after it, name might be empty.
    # Our regex: (?:to|as|at|into|還原到|存檔為|叫作|到|為)\s*([a-zA-Z0-9_\-\.]+)
    # "某個地方" contains non-alphanumeric chars for the regex match [a-zA-Z0-9_\-\.]

    assert result.matched_tool == "boring_checkpoint"
    assert result.suggested_params["action"] == "restore"
    # "某個地方" doesn't match [a-zA-Z0-9_\-\.]
    assert "name" not in result.suggested_params
    assert "_note" in result.suggested_params
