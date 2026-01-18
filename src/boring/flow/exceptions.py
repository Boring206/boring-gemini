class FlowError(Exception):
    """
    Critical error in the flow that strictly halts execution.
    Used for guardrail violations, implementation gaps, or safety checks.
    """

    pass


class GuardrailError(FlowError):
    """Specific error for PreFlightCheck violations."""

    pass
