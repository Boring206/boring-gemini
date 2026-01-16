# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from boring.cli.watch import BoringEventHandler
from boring.models import VerificationResult


@pytest.fixture
def mock_verifier():
    with patch("boring.cli.watch.CodeVerifier") as mock:
        yield mock


def test_watch_handler_ignores_irrelevant_files(mock_verifier, tmp_path):
    handler = BoringEventHandler(tmp_path)
    mock_event = MagicMock()
    mock_event.is_directory = False
    mock_event.src_path = str(tmp_path / "image.png")

    handler.on_modified(mock_event)

    # Should NOT classify or verify
    handler.verifier.verify_file.assert_not_called()


def test_watch_handler_delegates_to_verifier(mock_verifier, tmp_path):
    handler = BoringEventHandler(tmp_path)
    mock_event = MagicMock()
    mock_event.is_directory = False
    mock_event.src_path = str(tmp_path / "main.py")

    # Setup mock return
    handler.verifier.verify_file.return_value = [
        VerificationResult(passed=True, check_type="lint", message="OK", details=[], suggestions=[])
    ]

    handler.on_modified(mock_event)

    # Should call verifier
    handler.verifier.verify_file.assert_called_once()
    args, _ = handler.verifier.verify_file.call_args
    assert Path(args[0]).name == "main.py"


def test_watch_handler_reports_failure(mock_verifier, capsys, tmp_path):
    handler = BoringEventHandler(tmp_path)
    mock_event = MagicMock()
    mock_event.is_directory = False
    mock_event.src_path = str(tmp_path / "broken.js")

    handler.verifier.verify_file.return_value = [
        VerificationResult(
            passed=False,
            check_type="lint",
            message="Syntax Error",
            details=["Line 1"],
            suggestions=[],
        )
    ]

    handler.on_modified(mock_event)

    captured = capsys.readouterr()
    assert "Sensinel detected change" in captured.out or "Sentinel detected change" in captured.out
    assert "Issues detected" in captured.out
    assert "Syntax Error" in captured.out
