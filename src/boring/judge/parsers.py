"""
JSON Extraction and Parsing for Judge
"""

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def extract_json(response: str) -> Optional[dict[str, Any]]:
    """Extract JSON from LLM response with robust parsing."""
    try:
        # Clean up markdown code blocks if present
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # Try to find JSON block
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = cleaned[start:end]
            return json.loads(json_str)
    except json.JSONDecodeError:
        logger.warning("Invalid JSON in response")
    except Exception as e:
        logger.error(f"Error during JSON extraction: {e}")
    return None
