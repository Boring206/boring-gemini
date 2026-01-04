# Copyright 2025 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
MCP Prompts for Boring.

Registers prompts that help users interact with the server.
"""

from pydantic import Field


def register_prompts(mcp):
    """Register prompts with the MCP server."""
    
    @mcp.prompt(
        name="plan_feature",
        description="Generate a plan for implementing a new feature"
    )
    def plan_feature(
        feature: str = Field(description="Description of the feature to implement")
    ) -> str:
        """Generate a feature implementation plan."""
        return f"""Please create a detailed implementation plan for the following feature:

**Feature:** {feature}

Include:
1. Files to create/modify
2. Step-by-step implementation steps
3. Testing strategy
4. Potential edge cases"""

    @mcp.prompt(
        name="review_code",
        description="Request a code review for specific files"
    )
    def review_code(
        file_path: str = Field(description="Path to the file to review")
    ) -> str:
        """Generate a code review request."""
        return f"""Please review the code in `{file_path}` for:

1. **Bugs**: Logic errors, edge cases, null checks
2. **Security**: Injection, auth, data exposure
3. **Performance**: Inefficiencies, memory leaks
4. **Readability**: Naming, structure, documentation
5. **Best practices**: SOLID, DRY, testing"""

    @mcp.prompt(
        name="debug_error",
        description="Help debug an error message"
    )
    def debug_error(
        error_message: str = Field(description="The error message to debug")
    ) -> str:
        """Generate a debugging request."""
        return f"""Please help debug the following error:

```
{error_message}
```

Analyze:
1. Root cause
2. Likely culprits
3. Suggested fixes
4. Prevention strategies"""

    @mcp.prompt(
        name="refactor_code",
        description="Request refactoring suggestions"
    )
    def refactor_code(
        target: str = Field(description="What to refactor (file, function, class)")
    ) -> str:
        """Generate a refactoring request."""
        return f"""Please suggest refactoring improvements for: {target}

Focus on:
1. Code clarity
2. Maintainability
3. Performance
4. Testability"""

    @mcp.prompt(
        name="explain_code",
        description="Request code explanation"
    )
    def explain_code(
        code_path: str = Field(description="Path or name of code to explain")
    ) -> str:
        """Generate a code explanation request."""
        return f"""Please explain how `{code_path}` works:

1. Purpose and responsibility
2. Key algorithms/patterns used
3. How it fits into the larger system
4. Important edge cases handled"""
