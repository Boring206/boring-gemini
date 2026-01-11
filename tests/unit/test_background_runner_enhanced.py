
from unittest.mock import patch

from boring.loop.background_agent import BackgroundTaskRunner, get_runner, submit_background_task


class TestBackgroundRunnerEnhanced:
    """Enhanced tests for background task execution."""

    def test_runner_singleton(self):
        runner1 = get_runner()
        runner2 = get_runner()
        assert runner1 is runner2

    def test_submit_generic_task(self):
        runner = BackgroundTaskRunner(max_workers=1)

        def sample_func(x):
            return x * 2

        task_id = runner.submit(sample_func, 10, name="Double it")
        assert task_id.startswith("task-")

        result = runner.get_result(task_id, timeout=2)
        assert result["status"] == "completed"
        assert result["result"] == 20

    def test_task_not_found(self):
        runner = get_runner()
        status = runner.get_status("invalid-id")
        assert status["status"] == "not_found"

    def test_cancel_already_running(self):
        import time
        runner = BackgroundTaskRunner(max_workers=1)

        def slow_func():
            time.sleep(1)
            return "done"

        task_id = runner.submit(slow_func)
        time.sleep(0.1)  # Ensure it starts

        result = runner.cancel(task_id)
        # It's either running or already finished, so cannot cancel
        assert result["status"] == "cannot_cancel"

    @patch("boring.verification.CodeVerifier")
    def test_submit_verify_task(self, mock_verifier):
        mock_instance = mock_verifier.return_value
        mock_instance.verify_project.return_value = {"status": "SUCCESS"}

        result = submit_background_task("verify", task_args={"level": "FULL"})
        assert result["status"] == "submitted"
        assert result["task_type"] == "verify"

    def test_submit_unknown_task(self):
        result = submit_background_task("unknown_type")
        assert result["status"] == "error"

    def test_list_tasks_filter(self):
        runner = BackgroundTaskRunner(max_workers=1)
        runner.submit(lambda: 1, name="T1")

        tasks = runner.list_tasks(status_filter="pending")
        assert isinstance(tasks, list)
