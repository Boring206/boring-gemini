from ..skills_catalog import search_skills


class SkillsAdvisor:
    """
    Proactively advises on Skills/Extensions during the Design Phase.
    """

    def suggest_skills(self, goal: str) -> str:
        """
        Analyze the goal and return a formatted string of recommended skills.
        """
        # Use the existing catalog search
        results = search_skills(goal, limit=3)

        if not results:
            return ""

        suggestion = "\n\n💡 **Smart Skills Advice (Sage Mode)**:\n"
        suggestion += f"I found some skills that might help with '{goal}':\n"

        for skill in results:
            suggestion += (
                f"- **{skill.name}**: {skill.description_zh} (Install: `{skill.install_command}`)\n"
            )

        suggestion += "\nConsider adding these to your plan!"
        return suggestion
