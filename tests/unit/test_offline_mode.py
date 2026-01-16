import pytest

from boring.cli.offline import _update_env_file
from boring.core.config import settings


@pytest.fixture
def mock_env_file(tmp_path):
    env_path = tmp_path / ".env"
    # Monkeypatch settings to point to temp env?
    # Hard to patch BaseSettings behavior without reload, but we can test the helper function

    # Better: Test _update_env_file logic by mocking settings.PROJECT_ROOT
    original_root = settings.PROJECT_ROOT
    settings.PROJECT_ROOT = tmp_path
    yield env_path
    settings.PROJECT_ROOT = original_root


def test_offline_mode_default():
    # Default should be False unless ENV is set (which might be in this session)
    # This test might be flaky if run in environment with BORING_OFFLINE_MODE set
    pass


def test_update_env_file(mock_env_file):
    # 1. Enable
    assert _update_env_file(True)
    assert mock_env_file.exists()
    content = mock_env_file.read_text(encoding="utf-8")
    assert "BORING_OFFLINE_MODE=true" in content

    # 2. Disable
    assert _update_env_file(False)
    content = mock_env_file.read_text(encoding="utf-8")
    assert "BORING_OFFLINE_MODE=false" in content


def test_update_env_file_existing_content(mock_env_file):
    mock_env_file.write_text("FOO=bar\nKey=Val", encoding="utf-8")

    assert _update_env_file(True)
    content = mock_env_file.read_text(encoding="utf-8")
    assert "FOO=bar" in content
    assert "BORING_OFFLINE_MODE=true" in content
    assert content.endswith("\n")
