# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

import pytest
import boring
from boring.mcp.tool_router import get_tool_router

print(f"\nDEBUG: boring package path: {boring.__file__}")

def test_router_checkpoint_comprehensive():
    """Comprehensive test for checkpoint routing edge cases."""
    from boring.mcp import tool_router
    tool_router._router = None  # Reset singleton
    router = get_tool_router()
    
    scenarios = [
        # Restore variations
        ("幫我回退到 v1.2", "boring_checkpoint", "restore", "v1.2"),
        ("revert to baseline", "boring_checkpoint", "restore", "baseline"),
        ("還原到 stable-version", "boring_checkpoint", "restore", "stable-version"),
        ("rollback to previous-state", "boring_checkpoint", "restore", "previous-state"),
        
        # Create variations
        ("幫我存檔為 backup_2026", "boring_checkpoint", "create", "backup_2026"),
        ("save as point-A", "boring_checkpoint", "create", "point-A"),
        ("建立存檔 叫做 milestone-1", "boring_checkpoint", "create", "milestone-1"),
        ("標記當前狀態為 start", "boring_checkpoint", "create", "start"),
        
        # List variations
        ("有哪些存檔？", "boring_checkpoint", "list", None),
        ("show checkpoints", "boring_checkpoint", "list", None),
        ("哪個存檔可以用？", "boring_checkpoint", "list", None),
        ("清單列表", "boring_checkpoint", "list", None),
    ]
    
    for query, expected_tool, expected_action, expected_name in scenarios:
        result = router.route(query)
        assert result.matched_tool == expected_tool, f"Failed on query: '{query}'. Got '{result.matched_tool}' instead of '{expected_tool}' (Confidence: {result.confidence:.2f})"
        assert result.suggested_params.get("action") == expected_action, f"Wrong action for query: '{query}'. Got '{result.suggested_params.get('action')}'"
        if expected_name:
            assert result.suggested_params.get("name") == expected_name, f"Wrong name for query: '{query}'. Got '{result.suggested_params.get('name')}'"

def test_router_evaluation_routing():
    """Verify routing for the evaluation category."""
    from boring.mcp import tool_router
    tool_router._router = None  # Reset singleton
    router = get_tool_router()
    
    scenarios = [
        ("幫我評估這段程式碼", "boring_evaluate"),
        ("show bias report", "boring_bias_report"),
        ("generate evaluation rubric", "boring_generate_rubric"),
        ("查看評估指標", "boring_evaluation_metrics"),
        ("偏見報告", "boring_bias_report"),
        ("生成評分量表", "boring_generate_rubric"),
    ]
    
    for query, expected_tool in scenarios:
        result = router.route(query)
        assert result.matched_tool == expected_tool, f"Failed on evaluation query: {query}"

def test_router_checkpoint_safety_boost():
    """Verify that '救命' or 'checkpoint' boosts the git category significantly."""
    router = get_tool_router()
    
    # "救命" should trigger checkpoint (restore)
    result = router.route("救命！還原一下")
    assert result.matched_tool == "boring_checkpoint"
    assert result.suggested_params["action"] == "restore"
    
    # "救命" on its own should at least suggest listing checkpoints
    result = router.route("救命")
    assert result.matched_tool == "boring_checkpoint"
    assert result.suggested_params["action"] == "list"
