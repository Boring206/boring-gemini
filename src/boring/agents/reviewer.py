"""
Reviewer Agent - QA and Code Review Specialist

Responsibilities:
- Review code for bugs and issues
- Check for security vulnerabilities
- Verify edge case handling
- Act as "Devil's Advocate" - assume code is buggy

This agent NEVER approves easily. It finds problems.
"""

from pathlib import Path
from typing import List, Dict, Any

from .base import Agent, AgentRole, AgentContext, AgentMessage


class ReviewerAgent(Agent):
    """
    The Reviewer acts as a strict code reviewer.
    
    It receives code from the Coder and:
    1. Assumes code is buggy until proven otherwise
    2. Checks for security issues
    3. Verifies edge case handling
    4. Looks for breaking changes
    
    This is the "Devil's Advocate" agent.
    """
    
    def __init__(self, llm_client, project_root: Path = None):
        super().__init__(llm_client, AgentRole.REVIEWER)
        self.project_root = project_root or Path.cwd()
    
    @property
    def system_prompt(self) -> str:
        return """# You are the REVIEWER Agent (Devil's Advocate)

You are a paranoid security expert and senior code reviewer.
Your job is to FIND PROBLEMS. Assume ALL code is buggy.

## Your Mindset
- "This code probably has bugs. Where are they?"
- "What happens when things go wrong?"
- "How could a malicious user exploit this?"
- "What did the developer forget?"

## Review Checklist

### 1. Correctness
- Does it do what it claims to do?
- Are there off-by-one errors?
- Are comparisons correct (< vs <=)?
- Are return values handled properly?

### 2. Security
- SQL Injection?
- Path Traversal?
- Command Injection?
- Sensitive data exposure?
- Missing input validation?
- Hardcoded secrets?

### 3. Edge Cases
- What if input is None?
- What if input is empty?
- What if input is huge (DoS)?
- What if input has special characters?
- What if concurrent access?

### 4. Breaking Changes
- Does this change any public API?
- Are existing callers affected?
- Is the change backward compatible?

### 5. Performance
- Any obvious O(n²) loops?
- Unnecessary database calls?
- Memory leaks?

## Output Format

### 🔍 Review Summary
**Verdict:** [PASS | NEEDS_WORK | REJECT]

### Issues Found
- [🔴 CRITICAL] [Issue description] in `file:line`
- [🟠 MAJOR] [Issue description]
- [🟡 MINOR] [Issue description]

### Security Concerns
- [Concern 1]
- [Concern 2]

### Suggestions
- [Improvement 1]
- [Improvement 2]

### Verdict Rationale
Why you chose this verdict.

## Rules
- Be HARSH but FAIR
- Back up your claims with specifics
- Don't invent issues that don't exist
- PASS means "I tried hard to break it but couldn't"
- REJECT means "This is fundamentally broken"
- NEEDS_WORK means "Fixable issues exist"
"""
    
    async def execute(self, context: AgentContext) -> AgentMessage:
        """Review the code changes."""
        
        # Get the code output from Coder
        code_output = context.get_resource("code_output")
        modified_files = context.get_resource("modified_files") or []
        plan = context.get_current_plan()
        
        if not code_output:
            return AgentMessage(
                sender=self.role,
                receiver=AgentRole.ORCHESTRATOR,
                action="review_failed",
                summary="No code to review",
                artifacts={"error": "Missing code output"},
                requires_approval=False
            )
        
        # Build context about what we're reviewing
        files_context = ""
        if modified_files:
            files_context = f"""
## Files Being Reviewed
{chr(10).join(f'- {f}' for f in modified_files)}
"""
        
        plan_context = ""
        if plan:
            plan_context = f"""
## Original Plan (for verification)
{plan[:1500]}...
"""
        
        prompt = self._build_prompt(context, f"""
## Code to Review

{code_output[:8000]}{'...[truncated]' if len(code_output) > 8000 else ''}
{files_context}
{plan_context}

## Your Task

Review this code with extreme scrutiny:

1. Check EVERY function for bugs
2. Look for security vulnerabilities
3. Verify edge case handling
4. Compare against the plan - is anything missing?
5. Check for breaking changes

Be the Devil's Advocate. Try to BREAK this code.

End with a clear verdict: PASS, NEEDS_WORK, or REJECT.
""")
        
        response, success = await self._generate(prompt)
        
        if not success:
            return AgentMessage(
                sender=self.role,
                receiver=AgentRole.ORCHESTRATOR,
                action="review_failed",
                summary="Failed to generate review",
                artifacts={"error": response},
                requires_approval=False
            )
        
        # Parse the verdict
        verdict = self._extract_verdict(response)
        issues = self._extract_issues(response)
        
        # Store review in shared resources
        context.set_resource("code_review", response, self.role)
        context.set_resource("review_verdict", verdict, self.role)
        
        # Determine next agent
        if verdict == "PASS":
            next_agent = AgentRole.ORCHESTRATOR
            requires_approval = False
        elif verdict == "REJECT":
            next_agent = AgentRole.ARCHITECT  # Need to re-plan
            requires_approval = True
            approval_reason = "Code rejected - needs architectural review"
        else:  # NEEDS_WORK
            next_agent = AgentRole.CODER
            requires_approval = len(issues.get("critical", [])) > 0
            approval_reason = "Critical issues found - please review" if requires_approval else None
        
        return AgentMessage(
            sender=self.role,
            receiver=next_agent,
            action="review_completed",
            summary=f"{verdict}: {len(issues.get('critical', []))} critical, {len(issues.get('major', []))} major issues",
            artifacts={
                "verdict": verdict,
                "issues": issues,
                "review": response,
                "passed": verdict == "PASS"
            },
            requires_approval=requires_approval,
            approval_reason=approval_reason if requires_approval else None
        )
    
    def _extract_verdict(self, review: str) -> str:
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
    
    def _extract_issues(self, review: str) -> Dict[str, List[str]]:
        """Extract categorized issues from review text."""
        import re
        
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
