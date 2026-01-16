"""
Token and Cost Tracking Service (V13.0)

Provides estimation and tracking of token usage and associated costs
for various LLM models.
"""

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from boring.core.config import settings
from boring.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ModelPricing:
    """Pricing per 1M tokens (USD)."""

    input_price: float
    output_price: float


# Default pricing (approximate as of early 2025)
# Users can override this via config injection if needed
DEFAULT_PRICING = {
    "gemini-1.5-pro": ModelPricing(3.50, 10.50),  # Example pricing
    "gemini-1.5-flash": ModelPricing(0.35, 1.05),
    "gemini-2.0-flash": ModelPricing(0.35, 1.05),  # Assuming similar to 1.5 flash
    "claude-3-5-sonnet": ModelPricing(3.00, 15.00),
    "gpt-4o": ModelPricing(2.50, 10.00),
}


@dataclass
class UsageSession:
    """In-memory session stats."""

    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    call_count: int = 0
    model_breakdown: dict[str, dict[str, float]] = field(default_factory=dict)


class TokenTracker:
    """
    Tracks token usage and estimates costs.
    """

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or settings.PROJECT_ROOT
        self.stats_file = self.project_root / ".boring" / "usage_stats.json"
        self.session = UsageSession()
        self._ensure_storage()

    def _ensure_storage(self):
        if not self.stats_file.parent.exists():
            self.stats_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.stats_file.exists():
            self._save_stats({})

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate tokens using character count heuristic.
        Gemini/OpenAI avg ~4 chars per token for English text.
        """
        if not text:
            return 0
        return math.ceil(len(text) / 4.0)

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD."""
        # Normalize model name for lookup
        key = next((k for k in DEFAULT_PRICING if k in model.lower()), "gemini-1.5-flash")
        pricing = DEFAULT_PRICING.get(key, DEFAULT_PRICING["gemini-1.5-flash"])

        cost_input = (input_tokens / 1_000_000) * pricing.input_price
        cost_output = (output_tokens / 1_000_000) * pricing.output_price

        return cost_input + cost_output

    def track_usage(self, model: str, input_tokens: int, output_tokens: int):
        """Record usage for a call."""
        cost = self.calculate_cost(model, input_tokens, output_tokens)

        # Update session
        self.session.call_count += 1
        self.session.total_input_tokens += input_tokens
        self.session.total_output_tokens += output_tokens
        self.session.total_cost += cost

        if model not in self.session.model_breakdown:
            self.session.model_breakdown[model] = {"inputs": 0, "outputs": 0, "cost": 0.0}

        self.session.model_breakdown[model]["inputs"] += input_tokens
        self.session.model_breakdown[model]["outputs"] += output_tokens
        self.session.model_breakdown[model]["cost"] += cost

        # Persist to disk (cumulative)
        self._update_persistent_stats(model, input_tokens, output_tokens, cost)

    def _update_persistent_stats(self, model: str, in_tok: int, out_tok: int, cost: float):
        try:
            data = self.get_total_stats()

            # Update grand totals
            data["total_input_tokens"] = data.get("total_input_tokens", 0) + in_tok
            data["total_output_tokens"] = data.get("total_output_tokens", 0) + out_tok
            data["total_cost"] = data.get("total_cost", 0.0) + cost
            data["total_calls"] = data.get("total_calls", 0) + 1
            data["last_updated"] = __import__("datetime").datetime.now().isoformat()

            # Update breakdown
            breakdown = data.get("breakdown", {})
            if model not in breakdown:
                breakdown[model] = {"inputs": 0, "outputs": 0, "cost": 0.0}

            breakdown[model]["inputs"] += in_tok
            breakdown[model]["outputs"] += out_tok
            breakdown[model]["cost"] += cost
            data["breakdown"] = breakdown

            self._save_stats(data)
        except Exception as e:
            logger.error(f"Failed to update usage stats: {e}")

    def get_total_stats(self) -> dict:
        """Load persistent stats."""
        try:
            if self.stats_file.exists():
                return json.loads(self.stats_file.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _save_stats(self, data: dict):
        self.stats_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
