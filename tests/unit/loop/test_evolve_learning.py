# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from boring.loop.evolve import EvolveLoop


@patch("boring.loop.evolve.subprocess.run")
@patch("boring.intelligence.brain_manager.BrainManager")
def test_evolve_learns_on_success(mock_brain_cls, mock_run, tmp_path):
    # Setup
    mock_brain = mock_brain_cls.return_value
    mock_brain.learn_pattern.return_value = {"pattern_id": "TEST_ID"}

    mock_run.return_value.returncode = 0 # Immediate success

    # Run
    with patch("boring.loop.evolve.settings.PROJECT_ROOT", tmp_path):
        loop = EvolveLoop("Fix bug", "pytest")
        result = loop.run()

    # Assert
    assert result is True
    # Should initiate Brain
    mock_brain_cls.assert_called()
    # Should call learn_pattern
    mock_brain.learn_pattern.assert_called_once()
    args = mock_brain.learn_pattern.call_args[1]
    assert args["pattern_type"] == "evolution_success"
    assert "automated solution" in args["description"].lower()

@patch("boring.loop.evolve.subprocess.run")
@patch("boring.intelligence.brain_manager.BrainManager")
def test_evolve_does_not_learn_on_failure(mock_brain_cls, mock_run, tmp_path):
    # Always fail
    mock_run.return_value.returncode = 1

    with patch("boring.loop.evolve.EvolveLoop._run_agent_fix"), \
         patch("boring.loop.evolve.settings.PROJECT_ROOT", tmp_path):
        loop = EvolveLoop("Fix bug", "pytest", max_iterations=1)
        result = loop.run()

    assert result is False
    mock_brain_cls.assert_not_called()
