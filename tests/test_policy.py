from boring.core.policy import PolicyEngine, PolicyResult, PolicyRule
from boring.flow.nodes.base import BaseNode, FlowContext


class FailRule(PolicyRule):
    name = "FailAlways"

    def check(self, context) -> PolicyResult:
        return PolicyResult(False, "You shall not pass!")


class TestNode(BaseNode):
    def process(self, context):
        pass


def test_policy_enforcement(tmp_path):
    """VERIFY: Policy Engine strictly blocks node entry."""
    # Setup Context
    engine = PolicyEngine()
    engine.add_rule(FailRule())

    context = FlowContext(project_root=tmp_path, user_goal="Test Policy", policy_engine=engine)

    node = TestNode("Gatekeeper")

    # Check
    allowed, reason = node.can_enter(context)

    assert allowed is False
    assert "You shall not pass!" in reason
    assert "Policy Violation" in reason


def test_policy_pass(tmp_path):
    """VERIFY: Green policies allow entry."""
    engine = PolicyEngine()
    # No rules = pass

    context = FlowContext(project_root=tmp_path, user_goal="Test Policy", policy_engine=engine)

    node = TestNode("Gatekeeper")

    allowed, reason = node.can_enter(context)
    assert allowed is True
