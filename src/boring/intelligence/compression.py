"""
Context Compression - LLMLingua-style context optimization (V14.0)

This module provides advanced compression techniques to fit significantly more
information into the LLM context window.

Key Techniques:
1. Budget-aware Iterative Pruning
2. Structural Skeletonization (signatures-only mode)
3. Boilerplate & Fluff Removal
4. Identifier Mapping (Experimental)
5. Semantic Token Selective Context enrichment

Goal: 10x more code context availability.
"""

import logging
import re

from .context_optimizer import CHARS_PER_TOKEN, ContextSection

logger = logging.getLogger(__name__)


class ContextCompressor:
    """
    Advanced context compressor implementing budget-aware pruning and skeletonization.
    """

    def __init__(self, target_tokens: int = 4000):
        self.target_tokens = target_tokens
        self.compression_stats = {"original": 0, "compressed": 0, "ratio": 1.0, "tier_reached": 0}

    def compress_sections(self, sections: list[ContextSection]) -> str:
        """
        Compress a list of context sections to fit within target_tokens.
        """
        total_original = sum(s.token_count for s in sections)
        self.compression_stats["original"] = total_original

        if total_original <= self.target_tokens:
            return self._finalize(sections)

        # Iterative compression levels (Tiers)
        # Tier 1: Remove comments and whitespace
        # Tier 2: Collapse logs and docstrings
        # Tier 3: Collapse imports
        # Tier 4: Structural Skeleton (Keep signatures, collapse bodies)
        # Tier 5: Absolute Truncation

        tiers = [
            self._tier_basic_cleanup,
            self._tier_collapse_boilerplate,
            self._tier_skeletonize,
            self._tier_aggressive_truncation,
        ]

        current_sections = sections
        for i, tier_func in enumerate(tiers):
            self.compression_stats["tier_reached"] = i + 1
            logger.debug(f"Applying {tier_func.__name__}...")
            current_sections = [tier_func(s) for s in current_sections]
            current_total = sum(s.token_count for s in current_sections)
            logger.debug(f"Tier {i + 1} total: {current_total} tokens")

            if current_total <= self.target_tokens:
                break

        result = self._finalize(current_sections)
        self.compression_stats["compressed"] = len(result) // CHARS_PER_TOKEN
        self.compression_stats["ratio"] = (
            self.compression_stats["compressed"] / total_original if total_original > 0 else 1.0
        )

        logger.info(
            f"Context compressed: {total_original} -> {self.compression_stats['compressed']} tokens (Ratio: {self.compression_stats['ratio']:.2f})"
        )
        return result

    def _finalize(self, sections: list[ContextSection]) -> str:
        """Join sections into final string."""
        parts = []
        for s in sections:
            if s.source:
                parts.append(f"### {s.source}\n{s.content}")
            else:
                parts.append(s.content)
        return "\n\n".join(parts)

    def _tier_basic_cleanup(self, section: ContextSection) -> ContextSection:
        """Level 1: Remove comments and extra whitespace."""
        content = section.content
        # Remove comments (simple regex for Python/JS)
        content = re.sub(r"#.*$", "", content, flags=re.MULTILINE)
        content = re.sub(r"//.*$", "", content, flags=re.MULTILINE)
        # Remove extra blank lines
        content = re.sub(r"\n\s*\n", "\n", content)
        return self._update_section(section, content)

    def _tier_collapse_boilerplate(self, section: ContextSection) -> ContextSection:
        """Level 2: Collapse docstrings, logs, and imports."""
        content = section.content
        # Collapse docstrings
        content = re.sub(r'"""[\s\S]*?"""', '"""..."""', content)
        content = re.sub(r"'''[\s\S]*?'''", "'''...'''", content)
        # Collapse imports (if more than 3)
        import_lines = re.findall(r"^(?:from|import) .*$", content, re.MULTILINE)
        if len(import_lines) > 5:
            first = import_lines[0]
            last = import_lines[-1]
            content = re.sub(
                r"^(?:from|import) .*\n(?:(?:from|import) .*\n)+",
                f"{first}\n# ... {len(import_lines) - 2} imports ...\n{last}\n",
                content,
                count=1,
            )

        return self._update_section(section, content)

    def _tier_skeletonize(self, section: ContextSection) -> ContextSection:
        """Level 3: Keep only class/def signatures, remove bodies."""
        if section.section_type != "code":
            return section

        lines = section.content.split("\n")
        skeleton = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("def ", "class ", "async def ", "function ")):
                skeleton.append(line)
                if stripped.endswith(":"):
                    skeleton.append("    pass # ... body omitted")
            elif not line.startswith(" "):
                # Keep top level assignments etc if brief
                if len(line) < 100:
                    skeleton.append(line)

        return self._update_section(section, "\n".join(skeleton))

    def _tier_aggressive_truncation(self, section: ContextSection) -> ContextSection:
        """Level 4: Absolute character truncation."""
        # Calculate proportional budget for this section
        self.target_tokens * CHARS_PER_TOKEN
        # If we are here, we are desperate. Just take a chunk of the content.
        # Hard limit to 1000 chars per section if we are in this tier
        limit = 1000
        content = section.content[:limit] + "\n... (truncated)"
        return self._update_section(section, content)

    def _update_section(self, section: ContextSection, new_content: str) -> ContextSection:
        """Helper to create updated section."""
        return ContextSection(
            content=new_content,
            source=section.source,
            priority=section.priority,
            token_count=len(new_content) // CHARS_PER_TOKEN,
            content_hash=section.content_hash,
            section_type=section.section_type,
        )


def compress_context(sections: list[ContextSection], budget: int = 4000) -> str:
    """Stateless utility for context compression."""
    compressor = ContextCompressor(target_tokens=budget)
    return compressor.compress_sections(sections)
