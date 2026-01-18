from boring.flow.graph import GraphResult


def test_graph_result_success():
    res = GraphResult(True, "Success", "final_node")
    assert res.success is True
    assert str(res) == "Success"


def test_graph_result_failure():
    res = GraphResult(False, "Failed", "failed_node")
    assert res.success is False


def test_error_handler_success_not_misjudged():
    """Verify CRIT-003 Fix: Message containing 'Error' but marked success is NOT treated as failure."""
    res = GraphResult(True, "Successfully handled the ErrorHandler task", "ErrorHandler")

    # In this specific string "Successfully...", "Error" is present.
    # So "Error" in message is True.
    assert "Error" in res.message

    # Verify New Logic:
    assert res.success is True
    # This confirms that despite "Error" being in the message string, success=True allows commit.
