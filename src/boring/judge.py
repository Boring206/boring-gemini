import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import asdict

from .rubrics import Rubric, Criterion, CODE_QUALITY_RUBRIC
from .cli_client import GeminiCLIAdapter

logger = logging.getLogger(__name__)

class LLMJudge:
    """
    LLM-as-a-Judge implementation for evaluating code and plans.
    """
    
    def __init__(self, cli_adapter: GeminiCLIAdapter):
        self.cli = cli_adapter
        
    def grade_code(self, filename: str, content: str, rubric: Rubric = CODE_QUALITY_RUBRIC, interactive: bool = False) -> Dict[str, Any]:
        """
        Evaluate code quality against a rubric.
        If interactive=True, returns the PROMPT for the user to execute using their IDE AI.
        Else, executes via CLI adapter.
        """
        prompt = self._build_grade_prompt(filename, content, rubric)
        
        if interactive:
            # Return the prompts for the host AI (Cursor) to run
            return {
                "score": 0,
                "status": "pending_manual_review",
                "reasoning": "Delegated to Host AI",
                "prompt": prompt
            }
        
        try:
            # Call Gemini (in JSON mode)
            response = self.cli.chat(prompt, interactive=False)
            
            # Simple JSON extraction (assuming CLI returns mostly JSON)
            # In a real scenario, use a stricter JSON parser/cleaner
            try:
                # Find JSON block
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    result = json.loads(json_str)
                    return result
                else:
                    logger.warning("No JSON found in judge response")
                    return {"score": 0, "reasoning": "Failed to parse judge response", "raw": response}
            except json.JSONDecodeError:
                logger.warning("Invalid JSON from judge")
                return {"score": 0, "reasoning": "Invalid JSON response", "raw": response}
                
        except Exception as e:
            logger.error(f"Judge failed: {e}")
            return {"score": 0, "reasoning": str(e)}

    def compare_plans(self, plan_a: str, plan_b: str, context: str, interactive: bool = False) -> Dict[str, Any]:
        """
        Compare two implementation plans and pick a winner.
        
        Implements Pairwise Comparison with Position Bias Mitigation:
        1. First pass: Plan A in position 1, Plan B in position 2
        2. Second pass: Plan B in position 1, Plan A in position 2
        3. Consistency check: If passes disagree, return TIE with reduced confidence
        4. Final verdict: Consistent winner with averaged confidence
        
        Args:
            plan_a: First implementation plan
            plan_b: Second implementation plan
            context: Context/requirements for comparison
            interactive: If True, returns prompts for manual execution
            
        Returns:
            Dict with winner, confidence, positionConsistency, and reasoning
        """
        
        def build_comparison_prompt(first_plan: str, second_plan: str, first_label: str, second_label: str) -> str:
            return f'''You are an expert Software Architect Judge comparing two implementation plans.

## Critical Instructions
- Do NOT prefer plans because they are longer
- Do NOT prefer plans based on position (first vs second)
- Focus ONLY on quality according to the specified criteria
- Ties are acceptable when plans are genuinely equivalent

## Context
{context}

## Plan {first_label} (First Position)
{first_plan}

## Plan {second_label} (Second Position)
{second_plan}

## Comparison Criteria
1. **Feasibility**: Can this plan be realistically implemented?
2. **Simplicity**: Is the approach straightforward without unnecessary complexity?
3. **Completeness**: Does the plan address all requirements?
4. **Maintainability**: Will the result be easy to maintain?

## Instructions
1. Analyze each plan independently first
2. Compare them on each criterion
3. Determine overall winner with confidence level

## Output Format (JSON ONLY)
{{
    "winner": "{first_label}" or "{second_label}" or "TIE",
    "confidence": <float 0.0-1.0>,
    "criteria_comparison": {{
        "feasibility": {{ "winner": "...", "reasoning": "..." }},
        "simplicity": {{ "winner": "...", "reasoning": "..." }},
        "completeness": {{ "winner": "...", "reasoning": "..." }},
        "maintainability": {{ "winner": "...", "reasoning": "..." }}
    }},
    "overall_reasoning": "..."
}}'''

        if interactive:
            # Return both prompts for manual execution
            return {
                "status": "pending_manual_review",
                "prompts": {
                    "pass1": build_comparison_prompt(plan_a, plan_b, "A", "B"),
                    "pass2": build_comparison_prompt(plan_b, plan_a, "B", "A")
                },
                "instructions": "Execute both prompts and compare results. If winners match, that's the final winner. If they differ, the result is TIE."
            }
        
        try:
            # First pass: A in position 1, B in position 2
            prompt_pass1 = build_comparison_prompt(plan_a, plan_b, "A", "B")
            response_pass1 = self.cli.chat(prompt_pass1, interactive=False)
            result_pass1 = self._extract_json(response_pass1)
            
            if not result_pass1:
                return {"winner": "TIE", "confidence": 0.0, "error": "Failed to parse first pass response"}
            
            # Second pass: B in position 1, A in position 2
            prompt_pass2 = build_comparison_prompt(plan_b, plan_a, "B", "A")
            response_pass2 = self.cli.chat(prompt_pass2, interactive=False)
            result_pass2 = self._extract_json(response_pass2)
            
            if not result_pass2:
                return {"winner": "TIE", "confidence": 0.0, "error": "Failed to parse second pass response"}
            
            # Extract winners (normalize to A/B/TIE)
            winner_pass1 = result_pass1.get("winner", "TIE").upper()
            winner_pass2 = result_pass2.get("winner", "TIE").upper()
            
            conf_pass1 = float(result_pass1.get("confidence", 0.5))
            conf_pass2 = float(result_pass2.get("confidence", 0.5))
            
            # Position Bias Mitigation: Check consistency
            # In pass2, if the winner is the same plan, it should be consistent
            # E.g., if pass1 says "A" wins, pass2 (with B first) should also say "A" wins
            consistent = (winner_pass1 == winner_pass2)
            
            if consistent:
                final_winner = winner_pass1
                # Average confidence when consistent
                final_confidence = (conf_pass1 + conf_pass2) / 2
            else:
                # Passes disagree - position bias detected, return TIE
                final_winner = "TIE"
                final_confidence = 0.5
            
            return {
                "winner": final_winner,
                "confidence": round(final_confidence, 2),
                "positionConsistency": {
                    "consistent": consistent,
                    "pass1": {"winner": winner_pass1, "confidence": conf_pass1},
                    "pass2": {"winner": winner_pass2, "confidence": conf_pass2}
                },
                "reasoning": result_pass1.get("overall_reasoning", "") if consistent else "Position bias detected - inconsistent results across passes"
            }
            
        except Exception as e:
            logger.error(f"Plan comparison failed: {e}")
            return {"winner": "TIE", "confidence": 0.0, "error": str(e)}
    
    def _extract_json(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response with robust parsing."""
        try:
            # Try to find JSON block
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in response")
        return None

    def _build_grade_prompt(self, filename: str, content: str, rubric: Rubric) -> str:
        criteria_text = "\n".join([f"- {c.name}: {c.description} (Weight: {c.weight})" for c in rubric.criteria])
        
        return f'''
        You are a Senior Code Reviewer. Evaluate this file: {filename}
        
        RUBRIC ({rubric.strictness}):
        {criteria_text}
        
        CODE:
        ```
        {content[:10000]} 
        ```
        (Truncated if too long)
        
        INSTRUCTIONS:
        1. Rate each criterion from 1-5.
        2. Calculate weighted average score.
        3. Provide specific improvement suggestions.
        
        OUTPUT JSON format ONLY:
        {{
            "score": <float 1.0-5.0>,
            "summary": "<short summary>",
            "breakdown": {{
                "<criterion_name>": {{ "score": <int>, "comment": "..." }}
            }},
            "suggestions": ["fix 1", "fix 2"]
        }}
        '''
