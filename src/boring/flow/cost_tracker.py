"""
Flow Cost Tracker.

Estimates API cost based on flow execution steps.
"""

from dataclasses import dataclass


@dataclass
class CostModel:
    per_step_avg: float = 0.20  # Average $0.20 per step
    currency: str = "USD"


class FlowCostTracker:
    def __init__(self):
        self.total_steps = 0
        self.total_estimated_cost = 0.0
        self.model = CostModel()

    def track_step(self, node_name: str):
        """Record a step execution."""
        self.total_steps += 1
        # Simple estimation: linear cost
        # Future: vary by node type (Architect is more expensive than Setup)
        step_cost = self.model.per_step_avg
        if node_name == "Architect":
            step_cost = 0.50
        elif node_name == "Builder":
            step_cost = 0.30

        self.total_estimated_cost += step_cost

    def get_report(self) -> str:
        """Get cost summary."""
        return f"${self.total_estimated_cost:.2f} {self.model.currency} (Est.)"
