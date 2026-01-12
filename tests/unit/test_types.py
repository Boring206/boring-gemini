"""
Test suite for boring.types module.

Tests for BoringResult TypedDict and helper functions.
"""

from boring.types import BoringResult, create_error_result, create_success_result


class TestBoringResult:
    """Test cases for BoringResult TypedDict structure."""

    def test_success_result_structure(self):
        """Test that success result has correct structure."""
        result: BoringResult = {
            "status": "success",
            "message": "Operation completed",
            "data": {"key": "value"},
            "error": None,
        }
        assert result["status"] == "success"
        assert result["message"] == "Operation completed"
        assert result["data"] == {"key": "value"}
        assert result["error"] is None

    def test_error_result_structure(self):
        """Test that error result has correct structure."""
        result: BoringResult = {
            "status": "error",
            "message": "Operation failed",
            "data": None,
            "error": "Connection timeout",
        }
        assert result["status"] == "error"
        assert result["message"] == "Operation failed"
        assert result["data"] is None
        assert result["error"] == "Connection timeout"

    def test_status_literal_values(self):
        """Test that status only accepts 'success' or 'error'."""
        # Both valid literals
        success_result: BoringResult = {
            "status": "success",
            "message": "OK",
            "data": None,
            "error": None,
        }
        error_result: BoringResult = {
            "status": "error",
            "message": "FAIL",
            "data": None,
            "error": "details",
        }
        assert success_result["status"] in ("success", "error")
        assert error_result["status"] in ("success", "error")


class TestCreateSuccessResult:
    """Test cases for create_success_result helper function."""

    def test_basic_success_result(self):
        """Test creating a basic success result."""
        result = create_success_result("Operation completed successfully")
        assert result["status"] == "success"
        assert result["message"] == "Operation completed successfully"
        assert result["data"] is None
        assert result["error"] is None

    def test_success_result_with_dict_data(self):
        """Test success result with dictionary data."""
        data = {"files_processed": 10, "errors": 0}
        result = create_success_result("Files processed", data)
        assert result["status"] == "success"
        assert result["message"] == "Files processed"
        assert result["data"] == data
        assert result["error"] is None

    def test_success_result_with_list_data(self):
        """Test success result with list data."""
        data = ["file1.py", "file2.py", "file3.py"]
        result = create_success_result("Found files", data)
        assert result["status"] == "success"
        assert result["data"] == data

    def test_success_result_with_nested_data(self):
        """Test success result with nested data structure."""
        data = {
            "summary": {"total": 100, "passed": 95, "failed": 5},
            "details": [{"test": "test_a", "status": "pass"}, {"test": "test_b", "status": "fail"}],
        }
        result = create_success_result("Test results", data)
        assert result["data"]["summary"]["total"] == 100
        assert len(result["data"]["details"]) == 2

    def test_success_result_with_empty_string_message(self):
        """Test success result with empty message."""
        result = create_success_result("")
        assert result["status"] == "success"
        assert result["message"] == ""

    def test_success_result_with_unicode_message(self):
        """Test success result with Unicode message."""
        result = create_success_result("操作成功完成 ✅")
        assert result["status"] == "success"
        assert "✅" in result["message"]


class TestCreateErrorResult:
    """Test cases for create_error_result helper function."""

    def test_basic_error_result(self):
        """Test creating a basic error result."""
        result = create_error_result("Operation failed")
        assert result["status"] == "error"
        assert result["message"] == "Operation failed"
        assert result["data"] is None
        assert result["error"] is None

    def test_error_result_with_details(self):
        """Test error result with error details."""
        result = create_error_result(
            "Database connection failed", "Connection refused on port 5432"
        )
        assert result["status"] == "error"
        assert result["message"] == "Database connection failed"
        assert result["error"] == "Connection refused on port 5432"

    def test_error_result_with_long_details(self):
        """Test error result with long error details (stack trace)."""
        stack_trace = """Traceback (most recent call last):
  File "app.py", line 10, in main
    raise ValueError("Invalid input")
ValueError: Invalid input"""
        result = create_error_result("Execution error", stack_trace)
        assert "Traceback" in result["error"]
        assert "ValueError" in result["error"]

    def test_error_result_with_unicode_message(self):
        """Test error result with Unicode message."""
        result = create_error_result("操作失敗 ❌", "連接逾時")
        assert result["status"] == "error"
        assert "❌" in result["message"]
        assert "逾時" in result["error"]


class TestResultIntegration:
    """Integration tests for BoringResult workflow."""

    def test_result_can_be_serialized_to_json(self):
        """Test that results can be serialized to JSON."""
        import json

        success = create_success_result("OK", {"count": 42})
        error = create_error_result("FAIL", "details")

        # Should not raise
        success_json = json.dumps(success)
        error_json = json.dumps(error)

        # Should be parseable back
        assert json.loads(success_json) == success
        assert json.loads(error_json) == error

    def test_result_dict_access(self):
        """Test dictionary-style access to result fields."""
        result = create_success_result("Done", {"value": 123})

        # Dict-style access
        assert result.get("status") == "success"
        assert result.get("nonexistent") is None
        assert "status" in result
        assert "message" in result
        assert "data" in result
        assert "error" in result

    def test_result_iteration(self):
        """Test that result keys can be iterated."""
        result = create_success_result("Test")
        keys = list(result.keys())

        assert "status" in keys
        assert "message" in keys
        assert "data" in keys
        assert "error" in keys

    def test_result_values(self):
        """Test result values access."""
        result = create_success_result("Test", {"x": 1})
        values = list(result.values())

        assert "success" in values
        assert "Test" in values

    def test_result_items(self):
        """Test result items access."""
        result = create_error_result("Error", "details")
        items = dict(result.items())

        assert items["status"] == "error"
        assert items["error"] == "details"
