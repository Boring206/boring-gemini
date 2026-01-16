from typing import Any, Literal, TypedDict


class BoringResult(TypedDict):
    """
    Standardized return type for all Boring MCP tools.

    Attributes:
        status: "success" or "error"
        message: Human-readable description of the result
        data: Optional structured data (dict, list, etc.)
        error: Optional error details (if status is "error")
    """

    status: Literal["success", "error"]
    message: str
    data: Any | None
    error: str | None


def create_success_result(message: str, data: Any | None = None) -> BoringResult:
    """Helper to create a success result."""
    return {"status": "success", "message": message, "data": data, "error": None}


def create_error_result(message: str, error_details: str | None = None) -> BoringResult:
    """Helper to create an error result."""
    return {"status": "error", "message": message, "data": None, "error": error_details}
