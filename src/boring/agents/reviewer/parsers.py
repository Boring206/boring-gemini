"""
Reviewer Result Parsers
"""

import re
import json
from typing import List, Dict, Any

def extract_verdict(review: str) -> str:
    """Extract verdict from review text."""
    review_upper = review.upper()
    
    if "VERDICT:** PASS" in review_upper or "VERDICT: PASS" in review_upper:
        return "PASS"
    elif "VERDICT:** REJECT" in review_upper or "VERDICT: REJECT" in review_upper:
        return "REJECT"
    elif "VERDICT:** NEEDS_WORK" in review_upper or "VERDICT: NEEDS_WORK" in review_upper:
        return "NEEDS_WORK"
    
    # Fallback heuristics
    if "CRITICAL]" in review_upper:
        return "NEEDS_WORK"
    elif "PASS" in review_upper and "REJECT" not in review_upper:
        return "PASS"
    
    return "NEEDS_WORK"  # Default to cautious

def extract_issues(review: str) -> Dict[str, List[str]]:
    """Extract categorized issues from review text."""
    issues = {
        "critical": [],
        "major": [],
        "minor": [],
        "security": []
    }
    
    # Extract by markers
    critical_pattern = r'\[🔴 CRITICAL\]\s*(.+?)(?:\n|$)'
    major_pattern = r'\[🟠 MAJOR\]\s*(.+?)(?:\n|$)'
    minor_pattern = r'\[🟡 MINOR\]\s*(.+?)(?:\n|$)'
    
    issues["critical"] = re.findall(critical_pattern, review)
    issues["major"] = re.findall(major_pattern, review)
    issues["minor"] = re.findall(minor_pattern, review)
    
    # Security section
    security_section = re.search(
        r'### Security Concerns\n(.*?)(?:###|$)', 
        review, 
        re.DOTALL
    )
    if security_section:
        security_items = re.findall(r'-\s*(.+?)(?:\n|$)', security_section.group(1))
        issues["security"] = security_items
    
    return issues
