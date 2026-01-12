from typing import Any, Literal, Optional, TypedDict


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
    data: Optional[Any]
    error: Optional[str]


def create_success_result(message: str, data: Optional[Any] = None) -> BoringResult:
    """Helper to create a success result."""
    return {"status": "success", "message": message, "data": data, "error": None}


def create_error_result(message: str, error_details: Optional[str] = None) -> BoringResult:
    """Helper to create an error result."""
    return {"status": "error", "message": message, "data": None, "error": error_details}
