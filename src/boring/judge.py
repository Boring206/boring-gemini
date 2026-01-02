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

    def compare_plans(self, plan_a: str, plan_b: str, context: str) -> Dict[str, Any]:
        """
        Compare two implementation plans and pick a winner.
        Implementation of Pairwise Comparison pattern.
        """
        prompt = f'''
        You are an expert Software Architect Judge. Compare these two plans.
        
        CONTEXT:
        {context}
        
        PLAN A:
        {plan_a}
        
        PLAN B:
        {plan_b}
        
        INSTRUCTIONS:
        1. Compare based on: Feasibility, Simplicity, Completeness.
        2. Ignore length bias (longer is not better).
        3. Select a winner.
        
        OUTPUT JSON:
        {{
            "winner": "A" or "B",
            "confidence": 0.0-1.0,
            "reasoning": "..."
        }}
        '''
        # (Implementation similar to grade_code, omitted for brevity in first pass)
        # For now return placeholder
        return {"winner": "A", "confidence": 0.5, "reasoning": "Not implemented"}

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
