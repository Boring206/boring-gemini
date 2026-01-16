from ..skills_catalog import search_skills


class SkillsAdvisor:
    """
    Proactively advises on Skills/Extensions during the Design Phase.
    """

    def suggest_skills(self, goal: str) -> str:
        """
        Analyze the goal and return a formatted string of recommended skills.
        Uses both the Universal Skill Loader (Local) and Catalog (External).
        """
        # 1. Check Local Universal Skills first
        try:
            from ..skills.universal_loader import UniversalSkillLoader

            loader = UniversalSkillLoader()
            best_match = loader.match(goal, threshold=2.0)
        except Exception:
            best_match = None

        suggestions = []
        if best_match:
            suggestions.append(
                f"💡 **Local Skill Found**: You have a skill for this!\n- **{best_match.name}**: {best_match.description} (Use `boring_skill_activate('{best_match.name}')`)\n"
            )

        # 2. Check External Catalog
        results = search_skills(goal, limit=3)
        if results:
            msg = "\n🔌 **Catalog Recommendations**:\n"
            for skill in results:
                cmd = skill.install_command or f"boring_skill_download(url='{skill.repo_url}')"
                msg += f"- **{skill.name}**: {skill.description_zh} (Install: `{cmd}`)\n"
            suggestions.append(msg)

        if not suggestions:
            return ""

        return "\n".join(suggestions) + "\nConsider using these to enhance your workflow!"
