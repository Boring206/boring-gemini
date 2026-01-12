import random


class VibeInterface:
    """
    The Ambiguity Resolution Layer.
    Translates 'Vibe' (Fuzzy Input) into 'Spec' (Concrete Action).
    """

    CASUAL_KEYWORDS = ["隨便", "不知道", "你決定", "看著辦", "unknown", "whatever", "random"]
    BEAUTIFY_KEYWORDS = ["漂亮", "美化", "好看", "pretty", "beautiful", "nice", "ui"]

    def resolve_ambiguity(self, user_input: str, project_type: str = "generic") -> str:
        """
        If user input is vague, generate a concrete suggestion.
        Otherwise return input as is.
        """
        user_input = user_input.lower().strip()

        # 1. Handle "Don't Know"
        if any(k in user_input for k in self.CASUAL_KEYWORDS):
            return self._generate_suggestion(project_type)

        # 2. Handle "Make it Pretty"
        if any(k in user_input for k in self.BEAUTIFY_KEYWORDS):
            return "Task: Install a modern UI library (e.g., Tailwind or MUI) and apply a consistent theme."

        return user_input

    def _generate_suggestion(self, project_type: str) -> str:
        """Active Suggestion Mode"""

        common_suggestions = [
            "Add a README.md with detailed usage instructions.",
            "Setup a CI/CD pipeline using GitHub Actions.",
            "Add a 'CONTRIBUTING.md' for open source guides.",
        ]

        web_suggestions = [
            "Create a responsive Dashboard layout.",
            "Implement Dark Mode toggle.",
            "Add a Login/Auth page.",
            "Optimize images and assets for performance.",
        ]

        python_suggestions = [
            "Add type hints (mypy) to all functions.",
            "Create a CLI entry point using Typer.",
            "Write comprehensive unit tests with Pytest.",
        ]

        pool = common_suggestions
        if "web" in project_type or "react" in project_type:
            pool.extend(web_suggestions)
        elif "python" in project_type:
            pool.extend(python_suggestions)

        # Pick one random idea to be "Creative"
        suggestion = random.choice(pool)
        return f"Suggestion: {suggestion} (Selected by Sage Mode)"
