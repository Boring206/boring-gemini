"""
Tests for skills advisor.
"""

from unittest.mock import MagicMock, patch

import pytest

from boring.flow.skills_advisor import SkillsAdvisor


class TestSkillsAdvisor:
    """Tests for SkillsAdvisor."""

    @pytest.fixture
    def advisor(self):
        return SkillsAdvisor()

    def test_suggest_skills_with_local_match(self, advisor):
        """Test suggesting skills with local match."""
        mock_skill = MagicMock()
        mock_skill.name = "test_skill"
        mock_skill.description = "Test description"

        with patch("boring.skills.universal_loader.UniversalSkillLoader") as mock_loader:
            mock_instance = MagicMock()
            mock_instance.match.return_value = mock_skill
            mock_loader.return_value = mock_instance

            with patch("boring.flow.skills_advisor.search_skills", return_value=[]):
                result = advisor.suggest_skills("test goal")
                assert "test_skill" in result
                assert "Local Skill Found" in result

    def test_suggest_skills_with_catalog(self, advisor):
        """Test suggesting skills from catalog."""
        mock_skill = MagicMock()
        mock_skill.name = "catalog_skill"
        mock_skill.description_zh = "Catalog description"
        mock_skill.install_command = "boring install catalog_skill"
        mock_skill.repo_url = "https://example.com/skill"

        with patch("boring.skills.universal_loader.UniversalSkillLoader", side_effect=Exception()):
            with patch("boring.flow.skills_advisor.search_skills", return_value=[mock_skill]):
                result = advisor.suggest_skills("test goal")
                assert "catalog_skill" in result
                assert "Catalog Recommendations" in result

    def test_suggest_skills_no_matches(self, advisor):
        """Test suggesting skills with no matches."""
        with patch("boring.skills.universal_loader.UniversalSkillLoader", side_effect=Exception()):
            with patch("boring.flow.skills_advisor.search_skills", return_value=[]):
                result = advisor.suggest_skills("test goal")
                assert result == ""
