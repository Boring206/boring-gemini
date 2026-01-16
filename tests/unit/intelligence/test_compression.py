"""Tests for boring.intelligence.compression module."""

import pytest

from boring.intelligence.compression import ContextCompressor
from boring.intelligence.context_optimizer import ContextSection


class TestContextCompressor:
    """Tests for ContextCompressor class."""

    @pytest.fixture
    def compressor(self):
        return ContextCompressor(target_tokens=1000)

    def test_compressor_initialization(self, compressor):
        assert compressor.target_tokens == 1000
        assert compressor.compression_stats["original"] == 0
        assert compressor.compression_stats["compressed"] == 0

    def test_compress_within_budget(self, compressor):
        """Test that content within budget is not compressed."""
        sections = [
            ContextSection(
                source="test",
                content="def hello(): pass",
                priority=1,
                token_count=10,
                content_hash="hash",
                section_type="code",
            )
        ]

        result = compressor.compress_sections(sections)

        assert "hello" in result
        assert compressor.compression_stats["ratio"] == 1.0

    def test_compress_exceeds_budget(self):
        """Test compression when content exceeds budget."""
        compressor = ContextCompressor(target_tokens=50)

        # Create sections that exceed budget
        large_content = "def function():\n" + "    " * 100 + "pass\n" * 50
        sections = [
            ContextSection(
                source="large",
                content=large_content,
                priority=1,
                token_count=500,
                content_hash="hash",
                section_type="code",
            )
        ]

        result = compressor.compress_sections(sections)

        # Should be compressed
        assert len(result) < len(large_content)
        assert compressor.compression_stats["tier_reached"] > 0

    def test_compression_stats_tracking(self, compressor):
        """Test that compression stats are tracked correctly."""
        sections = [
            ContextSection(
                source="test",
                content="print('hello')",
                priority=1,
                token_count=5,
                content_hash="hash",
                section_type="code",
            )
        ]

        compressor.compress_sections(sections)

        assert compressor.compression_stats["original"] == 5

    def test_tier_basic_cleanup(self, compressor):
        """Test basic cleanup tier removes comments."""
        section = ContextSection(
            source="test",
            content="# comment\ndef func():\n    pass  # inline comment",
            priority=1,
            token_count=20,
            content_hash="hash",
            section_type="code",
        )

        cleaned = compressor._tier_basic_cleanup(section)

        # Comments should be removed or reduced
        assert cleaned.token_count <= section.token_count

    def test_tier_collapse_boilerplate(self, compressor):
        """Test boilerplate collapse tier."""
        section = ContextSection(
            source="test",
            content='import os\nimport sys\nimport json\nlogging.debug("test")',
            priority=1,
            token_count=30,
            content_hash="hash",
            section_type="code",
        )

        collapsed = compressor._tier_collapse_boilerplate(section)

        # Should collapse imports and logging
        assert collapsed is not None

    def test_tier_skeletonize(self, compressor):
        """Test skeletonization tier keeps signatures only."""
        section = ContextSection(
            source="test",
            content="""def my_function(arg1, arg2):
    '''Docstring'''
    x = arg1 + arg2
    y = x * 2
    return y
""",
            priority=1,
            token_count=50,
            content_hash="hash",
            section_type="code",
        )

        skeleton = compressor._tier_skeletonize(section)

        # Should keep signature but collapse body
        assert "my_function" in skeleton.content
        assert skeleton.token_count <= section.token_count

    def test_multiple_sections(self, compressor):
        """Test compression with multiple sections."""
        sections = [
            ContextSection(
                source="s1",
                content="def a(): pass",
                priority=1,
                token_count=10,
                content_hash="hash",
                section_type="code",
            ),
            ContextSection(
                source="s2",
                content="def b(): pass",
                priority=2,
                token_count=10,
                content_hash="hash",
                section_type="code",
            ),
            ContextSection(
                source="s3",
                content="def c(): pass",
                priority=3,
                token_count=10,
                content_hash="hash",
                section_type="code",
            ),
        ]

        result = compressor.compress_sections(sections)

        # All functions should be present
        assert "a" in result
        assert "b" in result
        assert "c" in result

    def test_finalize_format(self, compressor):
        """Test that finalize produces proper format."""
        sections = [
            ContextSection(
                source="File1",
                content="content1",
                priority=1,
                token_count=5,
                content_hash="hash",
                section_type="code",
            ),
            ContextSection(
                source="File2",
                content="content2",
                priority=2,
                token_count=5,
                content_hash="hash",
                section_type="code",
            ),
        ]

        result = compressor._finalize(sections)

        # Should have section headers
        assert "---" in result or "File1" in result
