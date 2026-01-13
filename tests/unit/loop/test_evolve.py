# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock, patch

from boring.loop.evolve import EvolveLoop


@patch("boring.loop.evolve.subprocess.run")
def test_evolve_success_first_try(mock_run):
    # Setup successful verification
    mock_run.return_value.returncode = 0

    loop = EvolveLoop(goal="Fix tests", verify_cmd="pytest")
    result = loop.run()

    assert result is True
    # Should verify once
    mock_run.assert_called_once()
    # Verify shlex splitting was used (args should be list)
    args, _ = mock_run.call_args
    assert isinstance(args[0], list)
    assert args[0] == ["pytest"]

@patch("boring.loop.evolve.subprocess.run")
@patch("boring.loop.evolve.EvolveLoop._run_agent_fix")
def test_evolve_retry_logic(mock_fix, mock_run):
    # Fail once then succeed
    fail_result = MagicMock(returncode=1, stderr="Error")
    success_result = MagicMock(returncode=0)
    mock_run.side_effect = [fail_result, success_result]

    loop = EvolveLoop(goal="Fix tests", verify_cmd="pytest", max_iterations=3)
    result = loop.run()

    assert result is True
    assert mock_run.call_count == 2
    assert mock_fix.call_count == 1  # Should triggers fix once

@patch("boring.loop.evolve.subprocess.run")
@patch("boring.loop.evolve.EvolveLoop._run_agent_fix")
def test_evolve_max_iterations(mock_fix, mock_run):
    # Always fail
    mock_run.return_value.returncode = 1
    mock_run.return_value.stderr = "Fail"

    loop = EvolveLoop(goal="Fix tests", verify_cmd="pytest", max_iterations=2)
    result = loop.run()

    assert result is False
    assert mock_run.call_count == 2
    assert mock_fix.call_count == 2
