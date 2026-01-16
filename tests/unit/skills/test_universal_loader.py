import pytest

from boring.skills.universal_loader import UniversalSkillLoader


@pytest.fixture
def mock_project_root(tmp_path):
    # Setup mock structure
    (tmp_path / ".boring/skills/skill-a").mkdir(parents=True)
    (tmp_path / ".gemini/skills/skill-b").mkdir(parents=True)

    # Define a skill with frontmatter
    skill_a_content = """---
name: skill-a
description: A boring skill
---
# Content A
"""
    (tmp_path / ".boring/skills/skill-a/SKILL.md").write_text(skill_a_content, encoding="utf-8")

    # Define another skill
    skill_b_content = """---
name: skill-b
description: A gemini skill
---
# Content B
"""
    (tmp_path / ".gemini/skills/skill-b/SKILL.md").write_text(skill_b_content, encoding="utf-8")

    return tmp_path


def test_discover_skills(mock_project_root):
    loader = UniversalSkillLoader(project_root=mock_project_root)
    skills = loader.discover_all()

    assert len(skills) == 2
    names = {s.name for s in skills}
    assert "skill-a" in names
    assert "skill-b" in names


def test_skill_attributes(mock_project_root):
    loader = UniversalSkillLoader(project_root=mock_project_root)
    skill = loader.load_by_name("skill-a")

    assert skill is not None
    assert skill.name == "skill-a"
    assert skill.description == "A boring skill"
    assert skill.platform == "boring"
    assert "# Content A" in skill.content


def test_match_skill(mock_project_root):
    loader = UniversalSkillLoader(project_root=mock_project_root)

    # Match by name
    match1 = loader.match("I want to use skill-a")
    assert match1 is not None and match1.name == "skill-a"

    # Match by description keyword
    match2 = loader.match("I need a gemini skill")
    assert match2 is not None and match2.name == "skill-b"
