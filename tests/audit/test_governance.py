import pytest

from boring.core.kernel import BoringKernel
from boring.flow.graph import FlowGraph
from boring.flow.nodes.base import BaseNode, FlowContext, NodeResult, NodeResultStatus


class RestrictedNode(BaseNode):
    def can_enter(self, context: FlowContext) -> tuple[bool, str]:
        # Simulate a Policy: "No execution on Fridays" or "Requires valid signature"
        # Here: Strict check failing
        return False, "POLICY_VIOLATION: Root access prohibited"

    async def process(self, context) -> NodeResult:
        return NodeResult(status=NodeResultStatus.SUCCESS, message="I should not run")


@pytest.mark.asyncio
async def test_governance_is_authoritative(tmp_path):
    """VERIFY: Policy violations (can_enter=False) strictly halt execution."""
    kernel = BoringKernel(tmp_path)
    ctx = kernel.create_context("Governance Test")

    graph = FlowGraph(ctx)
    graph.add_node(RestrictedNode("RestrictedArea"), is_start=True)

    result = await graph.run()

    # Assert authoritative blocking
    assert "POLICY_VIOLATION" in result.message
    assert "Flow Halted" in result.message

    # This proves that 'can_enter' is a hard gate, not an advisory warning.
    # Thus, the system is Governable.
