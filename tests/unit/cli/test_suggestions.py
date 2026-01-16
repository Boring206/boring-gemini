# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

import pytest

from boring.cli.suggestions import SuggestionEngine


@pytest.fixture
def mock_path(tmp_path):
    return tmp_path


def test_detect_project_type(mock_path):
    engine = SuggestionEngine(mock_path)

    # Empty
    assert engine._detect_project_type() == "generic"

    # Python
    (mock_path / "pyproject.toml").touch()
    assert engine._detect_project_type() == "python"

    # Node - Removing pyproject to avoid ambiguity or priority logic check
    (mock_path / "pyproject.toml").unlink()
    (mock_path / "package.json").touch()
    assert engine._detect_project_type() == "node"


@patch("boring.cli.suggestions.subprocess.run")
def test_has_uncommitted_changes(mock_run, mock_path):
    engine = SuggestionEngine(mock_path)

    # Case: Changes exist
    mock_run.return_value.stdout = "M modified_file.py"
    assert engine._has_uncommitted_changes() is True

    # Case: Clean
    mock_run.return_value.stdout = ""
    assert engine._has_uncommitted_changes() is False


@patch("boring.cli.suggestions.SuggestionEngine._detect_project_type")
@patch("boring.cli.suggestions.SuggestionEngine._has_uncommitted_changes")
def test_analyze_suggestions(mock_changes, mock_type, mock_path):
    engine = SuggestionEngine(mock_path)

    # Setup: Python project, uncommitted changes, last command was fix
    mock_type.return_value = "python"
    mock_changes.return_value = True

    suggestions = engine.analyze(last_command="fix")

    cmds = [cmd for cmd, _ in suggestions]

    # Check expectation
    assert "boring check" in cmds
    assert "pytest" in cmds  # Polyglot suggestion
    assert "boring save" in cmds  # Git suggestion
    assert "boring evolve" not in cmds  # Not in flow/evolve mode
