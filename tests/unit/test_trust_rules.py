"""
Tests for trust_rules module.
"""

import pytest

from boring.trust_rules import TrustRule, TrustRuleManager, get_trust_manager


class TestTrustRule:
    """Tests for TrustRule class."""

    def test_trust_rule_matches_tool_name(self):
        """Test tool name matching."""
        rule = TrustRule(tool_name="boring_commit")
        assert rule.matches("boring_commit", {}) is True
        assert rule.matches("boring_verify", {}) is False

    def test_trust_rule_matches_wildcard(self):
        """Test wildcard matching."""
        rule = TrustRule(tool_name="*")
        assert rule.matches("boring_commit", {}) is True
        assert rule.matches("any_tool", {}) is True

    def test_trust_rule_matches_path_pattern(self):
        """Test path pattern matching."""
        rule = TrustRule(tool_name="*", path_pattern="src/*")
        assert rule.matches("write_file", {"file_path": "src/main.py"}) is True
        assert rule.matches("write_file", {"file_path": "tests/test.py"}) is False

    def test_trust_rule_to_dict(self):
        """Test rule serialization."""
        rule = TrustRule(
            tool_name="test_tool",
            path_pattern="src/*",
            max_severity="medium",
            description="Test rule",
        )
        d = rule.to_dict()
        assert d["tool_name"] == "test_tool"
        assert d["path_pattern"] == "src/*"
        assert d["max_severity"] == "medium"

    def test_trust_rule_from_dict(self):
        """Test rule deserialization."""
        data = {
            "tool_name": "test_tool",
            "path_pattern": "src/*",
            "max_severity": "medium",
            "description": "Test rule",
        }
        rule = TrustRule.from_dict(data)
        assert rule.tool_name == "test_tool"
        assert rule.path_pattern == "src/*"


class TestTrustRuleManager:
    """Tests for TrustRuleManager class."""

    @pytest.fixture
    def manager(self, tmp_path):
        return TrustRuleManager(tmp_path)

    def test_add_rule(self, manager):
        """Test adding a rule."""
        rule = manager.add_rule("boring_commit", description="Test")
        assert rule.tool_name == "boring_commit"
        assert len(manager.rules) == 1

    def test_remove_rule(self, manager):
        """Test removing a rule."""
        manager.add_rule("boring_commit")
        assert manager.remove_rule("boring_commit") is True
        assert len(manager.rules) == 0

    def test_check_trust_matches(self, manager):
        """Test trust checking with matching rule."""
        manager.add_rule("boring_commit", max_severity="high")
        rule = manager.check_trust("boring_commit", {}, severity="medium")
        assert rule is not None
        assert rule.tool_name == "boring_commit"

    def test_check_trust_no_match(self, manager):
        """Test trust checking with no matching rule."""
        manager.add_rule("boring_commit")
        rule = manager.check_trust("boring_verify", {})
        assert rule is None

    def test_check_trust_severity_threshold(self, manager):
        """Test severity threshold checking."""
        manager.add_rule("boring_commit", max_severity="medium")
        # High severity should not match medium threshold
        rule = manager.check_trust("boring_commit", {}, severity="high")
        assert rule is None
        # Medium severity should match
        rule = manager.check_trust("boring_commit", {}, severity="medium")
        assert rule is not None

    def test_list_rules(self, manager):
        """Test listing rules."""
        manager.add_rule("tool1")
        manager.add_rule("tool2", path_pattern="src/*")
        rules = manager.list_rules()
        assert len(rules) == 2

    def test_clear_rules(self, manager):
        """Test clearing all rules."""
        manager.add_rule("tool1")
        manager.add_rule("tool2")
        count = manager.clear_rules()
        assert count == 2
        assert len(manager.rules) == 0

    def test_persistence(self, tmp_path):
        """Test rule persistence."""
        manager1 = TrustRuleManager(tmp_path)
        manager1.add_rule("boring_commit", description="Test rule")

        # Create new manager instance
        manager2 = TrustRuleManager(tmp_path)
        assert len(manager2.rules) == 1
        assert manager2.rules[0].tool_name == "boring_commit"


class TestTrustManagerSingleton:
    """Tests for get_trust_manager singleton."""

    def test_get_trust_manager_singleton(self, tmp_path):
        """Test that get_trust_manager returns same instance."""
        manager1 = get_trust_manager(tmp_path)
        manager2 = get_trust_manager(tmp_path)
        assert manager1 is manager2

    def test_get_trust_manager_different_paths(self, tmp_path):
        """Test different paths get different managers."""
        path1 = tmp_path / "project1"
        path2 = tmp_path / "project2"
        manager1 = get_trust_manager(path1)
        manager2 = get_trust_manager(path2)
        assert manager1 is not manager2
