from boring.intelligence.auto_learner import (
    AutoLearner,
    ErrorSolutionPair,
    auto_learn_from_response,
    get_auto_learner,
)


class TestAutoLearner:
    """Test suite for AutoLearner."""

    def test_initialization(self, tmp_path):
        learner = AutoLearner(tmp_path)
        assert learner.project_root == tmp_path
        assert learner._pending_errors == []

    def test_analyze_response_python_error(self, tmp_path):
        learner = AutoLearner(tmp_path)
        response = "There was an Error: ValueError('Invalid input')\n\nI have fixed this by updated the validation logic."

        pairs = learner.analyze_response(response)
        assert len(pairs) == 1
        assert pairs[0].error_type == "python_error"
        assert "ValueError" in pairs[0].error_message
        assert "fixed" in pairs[0].solution_summary.lower()

    def test_analyze_response_import_error(self, tmp_path):
        learner = AutoLearner(tmp_path)
        response = "ImportError: No module named 'numpy'\n\nSuccessfully pip installed numpy."

        pairs = learner.analyze_response(response)
        assert len(pairs) == 1
        assert pairs[0].error_type == "import_error"
        assert "numpy" in pairs[0].error_message
        assert "pip install" in pairs[0].solution_summary.lower()

    def test_pending_error_handling(self, tmp_path):
        learner = AutoLearner(tmp_path)
        response = "SyntaxError: invalid syntax"

        # No solution in this response
        pairs = learner.analyze_response(response)
        assert len(pairs) == 0
        assert len(learner._pending_errors) == 1
        assert learner._pending_errors[0].error_type == "syntax_error"

        # Record success should resolve it
        resolved = learner.record_success(context="Fixed indentation issue")
        assert len(resolved) == 1
        assert resolved[0].solution_summary == "Fixed indentation issue"
        assert len(learner._pending_errors) == 0

    def test_find_solution_logic(self, tmp_path):
        learner = AutoLearner(tmp_path)
        sections = [
            "Just a comment",
            "I resolved the bug by changing the return value.",
            "Another section",
        ]
        solution = learner._find_solution(sections)
        assert solution is not None
        assert "resolved" in solution.lower()

    def test_get_auto_learner_singleton(self, tmp_path):
        learner1 = get_auto_learner(tmp_path)
        learner2 = get_auto_learner(tmp_path)
        assert learner1 is learner2

    def test_auto_learn_from_response_no_pattern(self, tmp_path):
        result = auto_learn_from_response(tmp_path, "Everything is fine.")
        assert result["status"] == "NO_PATTERNS"

    def test_record_success_empty_pending(self, tmp_path):
        learner = AutoLearner(tmp_path)
        resolved = learner.record_success()
        assert resolved == []

    def test_error_solution_pair_timestamp(self):
        pair = ErrorSolutionPair(error_type="test", error_message="msg", solution_summary="sol")
        assert pair.timestamp != ""
        assert "T" in pair.timestamp  # ISO format
