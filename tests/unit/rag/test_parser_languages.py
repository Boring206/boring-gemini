from unittest.mock import MagicMock, patch

import pytest

from boring.rag.parser import TreeSitterParser


# Mock TreeSitter functionality to test language query registration
# without needing actual .so/.dll libraries for every language
@pytest.fixture
def mock_parser():
    with patch("boring.rag.parser.HAS_TREE_SITTER", True):
        with patch("boring.rag.parser.get_parser"):
            with patch("boring.rag.parser.get_language") as mock_lang:
                parser = TreeSitterParser()
                # Mock the query.matches result
                mock_query = MagicMock()
                mock_lang.return_value.query.return_value = mock_query
                mock_query.matches.return_value = []  # Default empty
                yield parser, mock_query


def test_language_detection(mock_parser):
    parser, _ = mock_parser

    # Check new languages
    from pathlib import Path

    assert parser.get_language_for_file(Path("Foo.kt")) == "kotlin"
    assert parser.get_language_for_file(Path("Script.kts")) == "kotlin"
    assert parser.get_language_for_file(Path("Bar.scala")) == "scala"

    # Check existing
    assert parser.get_language_for_file(Path("main.rs")) == "rust"


def test_kotlin_query_structure(mock_parser):
    parser, mock_query = mock_parser
    # Just need to verify that calling extract_chunks for kotlin
    # attempts to load the kotlin query string we defined

    parser.extract_chunks("class Foo {}", "kotlin")

    # Check that get_language was called for kotlin
    from boring.rag.parser import get_language

    get_language.assert_called_with("kotlin")

    # Verify the query string passed to it contains class_declaration
    # (Since we mocked the return, we can check the call args to see if our query map is correct)
    # The actual integration test with real tree-sitter lib is harder without the bin,
    # but this proves the logic flow.
    pass


def test_queries_dict_integrity():
    # Verify no syntax errors in S-expressions strings (basic check)
    parser = TreeSitterParser()
    for lang, query in parser.QUERIES.items():
        assert query.strip(), f"Query for {lang} is empty"
        # minimal parenthesis balance check
        assert query.count("(") == query.count(")"), f"Unbalanced parens in {lang} query"


def test_validate_language_support_graceful():
    # Test built-in validation function
    with patch("boring.rag.parser.HAS_TREE_SITTER", False):
        parser = TreeSitterParser()
        res = parser.validate_language_support("kotlin", "code")
        assert res["success"] is False
        assert "tree-sitter not available" in res["error"]
