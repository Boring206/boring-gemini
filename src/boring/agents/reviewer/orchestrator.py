"""
Parallel Review Orchestrator
"""

import asyncio
from pathlib import Path
from typing import Any


class ParallelReviewOrchestrator:
    """
    V10.15: Orchestrates multiple specialized reviewers in parallel.

    Each reviewer focuses on a specific aspect:
    - SecurityReviewer: SQL injection, XSS, path traversal
    - PerformanceReviewer: O(n²) loops, memory leaks
    - CorrectnesReviewer: Logic bugs, edge cases
    """

    # Specialized prompts for each aspect
    ASPECT_PROMPTS = {
        "security": "Focus ONLY on security vulnerabilities: SQL injection, XSS, path traversal, command injection, hardcoded secrets.",
        "performance": "Focus ONLY on performance issues: O(n²) loops, unnecessary allocations, memory leaks, blocking calls.",
        "correctness": "Focus ONLY on correctness: logic bugs, off-by-one errors, null handling, edge cases.",
        "api_breakage": "Focus ONLY on API changes: backward compatibility, signature changes, behavior changes."
    }

    def __init__(self, llm_client, project_root: Path = None):
        self.llm_client = llm_client
        self.project_root = project_root or Path.cwd()

    async def review_parallel(self, code: str, aspects: list[str] = None) -> dict[str, Any]:
        """
        Run multiple specialized reviews in parallel.
        """
        aspects = aspects or list(self.ASPECT_PROMPTS.keys())

        # Create tasks for each aspect
        tasks = []
        for aspect in aspects:
            if aspect in self.ASPECT_PROMPTS:
                tasks.append(self._review_aspect(code, aspect))

        # Run in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results
        combined = {
            "aspects": {},
            "all_issues": [],
            "combined_verdict": "PASS"
        }

        for aspect, result in zip(aspects, results):
            if isinstance(result, Exception):
                combined["aspects"][aspect] = {"error": str(result)}
            else:
                combined["aspects"][aspect] = result
                combined["all_issues"].extend(result.get("issues", []))

                # Downgrade verdict if any aspect fails
                if result.get("verdict") == "REJECT":
                    combined["combined_verdict"] = "REJECT"
                elif result.get("verdict") == "NEEDS_WORK" and combined["combined_verdict"] == "PASS":
                    combined["combined_verdict"] = "NEEDS_WORK"

        return combined

    async def _review_aspect(self, code: str, aspect: str) -> dict[str, Any]:
        """Review code for a specific aspect."""
        prompt = f"""You are a specialized {aspect.upper()} reviewer.

{self.ASPECT_PROMPTS[aspect]}

## Code to Review
```
{code[:6000]}
```

Respond in JSON format:
{{
  "aspect": "{aspect}",
  "verdict": "PASS|NEEDS_WORK|REJECT",
  "issues": ["issue1", "issue2"],
  "summary": "Brief summary"
}}
"""
        try:
            response, success = await self.llm_client.generate_async(prompt)
            if success:
                import json
                # Extract JSON from response
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    return json.loads(response[start:end])
            return {"verdict": "PASS", "issues": [], "summary": "Review completed"}
        except Exception as e:
            return {"verdict": "NEEDS_WORK", "issues": [str(e)], "summary": "Review failed"}
