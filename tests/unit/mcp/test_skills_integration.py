from unittest.mock import MagicMock, patch

import pytest

from boring.mcp.tools.integration import boring_skills_install

# Mock data for SKILLS_CATALOG to isolate tests from real catalog changes
MOCK_SKILL_NAME = "test-skill"
MOCK_INSTALL_CMD = "echo install"


@pytest.fixture
def mock_catalog():
    with patch("boring.mcp.tools.integration.SKILLS_CATALOG") as mock_list:
        mock_skill = MagicMock()
        mock_skill.name = MOCK_SKILL_NAME
        mock_skill.install_command = MOCK_INSTALL_CMD
        mock_list.__iter__.return_value = [mock_skill]
        yield mock_list


def test_install_skill_success(mock_catalog):
    """Test successful installation of a skill."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "Installation complete"

        result = boring_skills_install(name=MOCK_SKILL_NAME)

        assert result["status"] == "SUCCESS"
        assert result["command"] == MOCK_INSTALL_CMD
        mock_run.assert_called_once()


def test_install_skill_not_found():
    """Test error when skill is not in catalog."""
    with patch("boring.mcp.tools.integration.SKILLS_CATALOG", []):
        result = boring_skills_install(name="non-existent-skill")

        assert result["status"] == "ERROR"
        assert "not found" in result["message"]


def test_install_skill_no_command(mock_catalog):
    """Test skipped status when skill has no install command."""
    # Modify mock to remove install command
    mock_catalog.__iter__.return_value[0].install_command = None

    result = boring_skills_install(name=MOCK_SKILL_NAME)

    assert result["status"] == "SKIPPED"
    assert "no automated install command" in result["message"]
