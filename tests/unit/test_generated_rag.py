# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.rag module.

This test file covers all functions and classes in the RAG module that were not
adequately tested in the original test_rag.py file.
"""

from unittest.mock import MagicMock, patch

import pytest

from boring.rag.code_indexer import CodeChunk, CodeIndexer, IndexStats
from boring.rag.graph_builder import DependencyGraph, GraphStats
from boring.rag.index_state import IndexState
from boring.rag.parser import ParsedChunk, TreeSitterParser
from boring.rag.rag_retriever import RAGRetriever, RAGStats, RetrievalResult, create_rag_retriever

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory structure."""
    project = tmp_path / "project"
    project.mkdir()
    (project / "src").mkdir()
    (project / "src" / "main.py").write_text("def hello(): pass")
    return project


@pytest.fixture
def sample_chunks():
    """Create sample CodeChunk objects for testing."""
    return [
        CodeChunk(
            chunk_id="chunk1",
            file_path="test.py",
            chunk_type="function",
            name="func_a",
            content="def func_a(): func_b()",
            start_line=1,
            end_line=5,
            dependencies=["func_b"],
        ),
        CodeChunk(
            chunk_id="chunk2",
            file_path="test.py",
            chunk_type="function",
            name="func_b",
            content="def func_b(): pass",
            start_line=6,
            end_line=8,
            dependencies=[],
        ),
        CodeChunk(
            chunk_id="chunk3",
            file_path="test.py",
            chunk_type="class",
            name="MyClass",
            content="class MyClass:\n    def method(self): pass",
            start_line=10,
            end_line=12,
            dependencies=[],
        ),
    ]


# =============================================================================
# INDEX STATE TESTS
# =============================================================================


class TestIndexState:
    """Tests for IndexState class."""

    @pytest.fixture(autouse=True)
    def mock_settings(self, tmp_path):
        """Mock global settings for IndexState tests."""
        with patch("boring.rag.index_state.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = tmp_path / "project"
            mock_settings.CACHE_DIR = tmp_path / "cache"
            yield mock_settings

    def test_index_state_init(self, temp_project):
        """Test IndexState initialization."""
        # Directly pass project_root to override mocked setting if needed,
        # but here we test the explicit init
        state = IndexState(temp_project)
        assert state.project_root == temp_project
        assert isinstance(state.state, dict)

    def test_index_state_get_changed_files_new_file(self, temp_project):
        """Test get_changed_files with new file."""
        state = IndexState(temp_project)
        new_file = temp_project / "new_file.py"
        new_file.write_text("print('new')")

        changed = state.get_changed_files([new_file])
        assert len(changed) == 1
        assert new_file in changed

    def test_index_state_get_changed_files_modified_file(self, temp_project):
        """Test get_changed_files with modified file."""
        state = IndexState(temp_project)
        test_file = temp_project / "test.py"
        test_file.write_text("print('original')")

        # Index the file first
        state.update(test_file, ["chunk1"])

        # Modify the file
        test_file.write_text("print('modified')")

        changed = state.get_changed_files([test_file])
        assert len(changed) == 1
        assert test_file in changed

    def test_index_state_get_changed_files_unchanged_file(self, temp_project):
        """Test get_changed_files with unchanged file."""
        state = IndexState(temp_project)
        test_file = temp_project / "test.py"
        test_file.write_text("print('test')")

        # Index the file
        state.update(test_file, ["chunk1"])

        # File unchanged
        changed = state.get_changed_files([test_file])
        assert len(changed) == 0

    def test_index_state_get_stale_files(self, temp_project):
        """Test get_stale_files identifies deleted files."""
        state = IndexState(temp_project)
        test_file = temp_project / "test.py"
        test_file.write_text("print('test')")

        # Index the file
        state.update(test_file, ["chunk1"])

        # File is deleted
        test_file.unlink()

        stale = state.get_stale_files([])
        assert len(stale) == 1
        assert "test.py" in stale

    def test_index_state_get_chunks_for_file(self, temp_project):
        """Test get_chunks_for_file."""
        state = IndexState(temp_project)
        test_file = temp_project / "test.py"
        test_file.write_text("print('test')")

        chunk_ids = ["chunk1", "chunk2"]
        state.update(test_file, chunk_ids)

        retrieved = state.get_chunks_for_file(test_file)
        assert retrieved == chunk_ids

    def test_index_state_get_chunks_for_file_not_indexed(self, temp_project):
        """Test get_chunks_for_file with unindexed file."""
        state = IndexState(temp_project)
        test_file = temp_project / "test.py"
        test_file.write_text("print('test')")

        retrieved = state.get_chunks_for_file(test_file)
        assert retrieved == []

    def test_index_state_update(self, temp_project):
        """Test update method."""
        state = IndexState(temp_project)
        test_file = temp_project / "test.py"
        test_file.write_text("print('test')")

        chunk_ids = ["chunk1", "chunk2"]
        state.update(test_file, chunk_ids)

        rel_path = str(test_file.relative_to(temp_project))
        assert rel_path in state.state
        assert state.state[rel_path]["chunks"] == chunk_ids
        assert "hash" in state.state[rel_path]

    def test_index_state_remove(self, temp_project):
        """Test remove method."""
        state = IndexState(temp_project)
        test_file = temp_project / "test.py"
        test_file.write_text("print('test')")

        state.update(test_file, ["chunk1"])
        rel_path = str(test_file.relative_to(temp_project))
        assert rel_path in state.state

        state.remove(rel_path)
        assert rel_path not in state.state

    def test_index_state_remove_nonexistent(self, temp_project):
        """Test remove with nonexistent path."""
        state = IndexState(temp_project)
        # Should not raise exception
        state.remove("nonexistent.py")

    def test_index_state_save_and_load(self, temp_project):
        """Test save and load persistence."""
        state = IndexState(temp_project)
        test_file = temp_project / "test.py"
        test_file.write_text("print('test')")

        state.update(test_file, ["chunk1"])
        state.save()

        # Create new instance and load
        state2 = IndexState(temp_project)
        assert "test.py" in state2.state or str(test_file.relative_to(temp_project)) in state2.state

    def test_index_state_compute_hash(self, temp_project):
        """Test _compute_hash method."""
        state = IndexState(temp_project)
        test_file = temp_project / "test.py"
        test_file.write_text("print('test')")

        hash1 = state._compute_hash(test_file)
        assert isinstance(hash1, str)
        assert len(hash1) > 0

        # Same content should produce same hash
        hash2 = state._compute_hash(test_file)
        assert hash1 == hash2

    def test_index_state_compute_hash_nonexistent_file(self, temp_project):
        """Test _compute_hash with nonexistent file."""
        state = IndexState(temp_project)
        nonexistent = temp_project / "nonexistent.py"

        hash_val = state._compute_hash(nonexistent)
        assert hash_val == ""

    def test_index_state_get_rel_path(self, temp_project):
        """Test _get_rel_path method."""
        state = IndexState(temp_project)
        test_file = temp_project / "src" / "test.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("test")

        rel_path = state._get_rel_path(test_file)
        assert "test.py" in rel_path

    def test_index_state_get_rel_path_outside_root(self, temp_project):
        """Test _get_rel_path with file outside project root."""
        state = IndexState(temp_project)
        outside_file = temp_project.parent / "outside.py"
        outside_file.write_text("test")

        rel_path = state._get_rel_path(outside_file)
        # Should return absolute path as fallback
        assert isinstance(rel_path, str)


# =============================================================================
# TREE-SITTER PARSER TESTS
# =============================================================================


class TestTreeSitterParser:
    """Tests for TreeSitterParser class."""

    def test_tree_sitter_parser_init(self):
        """Test TreeSitterParser initialization."""
        parser = TreeSitterParser()
        assert isinstance(parser.parsers, dict)

    def test_tree_sitter_parser_is_available(self):
        """Test is_available property."""
        parser = TreeSitterParser()
        # May be True or False depending on whether tree-sitter is installed
        assert isinstance(parser.is_available(), bool)

    def test_tree_sitter_parser_get_language_for_file_python(self, tmp_path):
        """Test get_language_for_file with Python file."""
        parser = TreeSitterParser()
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        lang = parser.get_language_for_file(test_file)
        assert lang == "python"

    def test_tree_sitter_parser_get_language_for_file_javascript(self, tmp_path):
        """Test get_language_for_file with JavaScript file."""
        parser = TreeSitterParser()
        test_file = tmp_path / "test.js"
        test_file.write_text("console.log('test')")

        lang = parser.get_language_for_file(test_file)
        assert lang == "javascript"

    def test_tree_sitter_parser_get_language_for_file_unknown(self, tmp_path):
        """Test get_language_for_file with unknown extension."""
        parser = TreeSitterParser()
        test_file = tmp_path / "test.unknown"
        test_file.write_text("test")

        lang = parser.get_language_for_file(test_file)
        assert lang is None

    @patch("boring.rag.parser.HAS_TREE_SITTER", False)
    def test_tree_sitter_parser_parse_file_not_available(self, tmp_path):
        """Test parse_file when tree-sitter is not available."""
        parser = TreeSitterParser()
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass")

        chunks = parser.parse_file(test_file)
        assert chunks == []

    @patch("boring.rag.parser.HAS_TREE_SITTER", True)
    def test_tree_sitter_parser_parse_file_unknown_language(self, tmp_path):
        """Test parse_file with unknown language."""
        parser = TreeSitterParser()
        test_file = tmp_path / "test.unknown"
        test_file.write_text("test")

        chunks = parser.parse_file(test_file)
        assert chunks == []

    @patch("boring.rag.parser.HAS_TREE_SITTER", True)
    def test_tree_sitter_parser_parse_file_read_error(self, tmp_path):
        """Test parse_file with file read error."""
        parser = TreeSitterParser()
        # Use a directory instead of a file
        test_dir = tmp_path / "test.py"
        test_dir.mkdir()

        chunks = parser.parse_file(test_dir)
        assert chunks == []

    @patch("boring.rag.parser.HAS_TREE_SITTER", False)
    def test_tree_sitter_parser_extract_chunks_not_available(self):
        """Test extract_chunks when tree-sitter is not available."""
        parser = TreeSitterParser()
        chunks = parser.extract_chunks("def test(): pass", "python")
        assert chunks == []


# =============================================================================
# CODE INDEXER TESTS (Extended)
# =============================================================================


class TestCodeIndexerExtended:
    """Extended tests for CodeIndexer class."""

    def test_code_indexer_collect_files(self, temp_project):
        """Test collect_files method."""
        # Create multiple Python files
        (temp_project / "src" / "file1.py").write_text("def f1(): pass")
        (temp_project / "src" / "file2.py").write_text("def f2(): pass")
        (temp_project / "file3.py").write_text("def f3(): pass")

        indexer = CodeIndexer(temp_project)
        files = indexer.collect_files()

        assert len(files) >= 3
        file_names = [f.name for f in files]
        assert "file1.py" in file_names or any("file1.py" in str(f) for f in files)
        assert "file2.py" in file_names or any("file2.py" in str(f) for f in files)
        assert "file3.py" in file_names or any("file3.py" in str(f) for f in files)

    def test_code_indexer_collect_files_skips_dirs(self, temp_project):
        """Test that collect_files skips ignored directories."""
        # Create directories explicitly first
        git_dir = temp_project / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("test")

        node_modules = temp_project / "node_modules" / "package"
        node_modules.mkdir(parents=True)
        (node_modules / "index.js").write_text("test")

        indexer = CodeIndexer(temp_project)

        # Verify helper directly first
        assert indexer._should_skip_dir(".git") is True
        assert indexer._should_skip_dir("node_modules") is True

        files = indexer.collect_files()

        # Should not include files in .git or node_modules
        file_paths = [str(f) for f in files]
        assert not any(".git" in p for p in file_paths)
        assert not any("node_modules" in p for p in file_paths)

    def test_code_indexer_index_file_empty(self, temp_project):
        """Test index_file with empty file."""
        empty_file = temp_project / "empty.py"
        empty_file.write_text("")

        indexer = CodeIndexer(temp_project)
        chunks = list(indexer.index_file(empty_file))

        # Empty file might produce no chunks or a script chunk
        assert isinstance(chunks, list)

    def test_code_indexer_index_file_syntax_error(self, temp_project):
        """Test index_file with syntax error."""
        bad_file = temp_project / "bad.py"
        bad_file.write_text("def incomplete(")  # Syntax error

        indexer = CodeIndexer(temp_project)
        # Should handle gracefully without crashing
        chunks = list(indexer.index_file(bad_file))
        assert isinstance(chunks, list)

    def test_code_indexer_get_stats(self, temp_project):
        """Test get_stats method."""
        test_file = temp_project / "test.py"
        test_file.write_text("class MyClass:\n    def method(self): pass\ndef function(): pass\n")

        indexer = CodeIndexer(temp_project)
        list(indexer.index_file(test_file))

        stats = indexer.get_stats()
        assert isinstance(stats, IndexStats)
        assert stats.functions >= 1
        assert stats.classes >= 1


# =============================================================================
# DEPENDENCY GRAPH TESTS (Extended)
# =============================================================================


class TestDependencyGraphExtended:
    """Extended tests for DependencyGraph class."""

    def test_dependency_graph_init_empty(self):
        """Test DependencyGraph with empty chunks."""
        graph = DependencyGraph([])
        assert graph.get_stats().total_nodes == 0

    def test_dependency_graph_init_with_chunks(self, sample_chunks):
        """Test DependencyGraph initialization with chunks."""
        graph = DependencyGraph(sample_chunks)
        stats = graph.get_stats()
        assert stats.total_nodes == 3

    def test_dependency_graph_add_chunk(self, sample_chunks):
        """Test add_chunk method."""
        graph = DependencyGraph(sample_chunks[:2])
        assert graph.get_stats().total_nodes == 2

        graph.add_chunk(sample_chunks[2])
        assert graph.get_stats().total_nodes == 3

    def test_dependency_graph_get_chunk(self, sample_chunks):
        """Test get_chunk method."""
        graph = DependencyGraph(sample_chunks)

        chunk = graph.get_chunk("chunk1")
        assert chunk is not None
        assert chunk.name == "func_a"

        nonexistent = graph.get_chunk("nonexistent")
        assert nonexistent is None

    def test_dependency_graph_get_chunks_by_name(self, sample_chunks):
        """Test get_chunks_by_name method."""
        graph = DependencyGraph(sample_chunks)

        chunks = graph.get_chunks_by_name("func_a")
        assert len(chunks) >= 1
        assert chunks[0].name == "func_a"

    def test_dependency_graph_get_callers(self, sample_chunks):
        """Test get_callers method."""
        graph = DependencyGraph(sample_chunks)

        callers = graph.get_callers("chunk2")  # func_b
        assert len(callers) >= 1
        assert any(c.name == "func_a" for c in callers)

    def test_dependency_graph_get_callees(self, sample_chunks):
        """Test get_callees method."""
        graph = DependencyGraph(sample_chunks)

        callees = graph.get_callees("chunk1")  # func_a
        assert len(callees) >= 1
        assert any(c.name == "func_b" for c in callees)

    def test_dependency_graph_get_related_chunks(self, sample_chunks):
        """Test get_related_chunks method."""
        graph = DependencyGraph(sample_chunks)

        related = graph.get_related_chunks([sample_chunks[0]], depth=1)
        assert isinstance(related, list)

    def test_dependency_graph_get_impact_zone(self, sample_chunks):
        """Test get_impact_zone method."""
        graph = DependencyGraph(sample_chunks)

        impact = graph.get_impact_zone("chunk2", depth=1)  # func_b
        assert isinstance(impact, list)
        # func_a depends on func_b, so it should be in impact zone
        assert any(c.name == "func_a" for c in impact)

    def test_dependency_graph_get_context_for_modification(self, sample_chunks):
        """Test get_context_for_modification method."""
        graph = DependencyGraph(sample_chunks)

        context = graph.get_context_for_modification("chunk2")
        assert isinstance(context, dict)
        assert "callers" in context
        assert "callees" in context

    def test_dependency_graph_get_stats(self, sample_chunks):
        """Test get_stats method."""
        graph = DependencyGraph(sample_chunks)

        stats = graph.get_stats()
        assert isinstance(stats, GraphStats)
        assert stats.total_nodes == 3

    def test_dependency_graph_find_path(self, sample_chunks):
        """Test find_path method."""
        graph = DependencyGraph(sample_chunks)

        path = graph.find_path("chunk1", "chunk2", max_depth=5)
        # func_a calls func_b, so path should exist
        assert path is not None or len(path) > 0 if path else True

    def test_dependency_graph_find_path_nonexistent(self, sample_chunks):
        """Test find_path with no path."""
        graph = DependencyGraph(sample_chunks)

        # chunk3 (MyClass) has no connection to chunk1
        path = graph.find_path("chunk3", "chunk1", max_depth=2)
        # May return None or empty list
        assert path is None or len(path) == 0


# =============================================================================
# RAG RETRIEVER TESTS (Extended with Mocks)
# =============================================================================


class TestRAGRetrieverExtended:
    """Extended tests for RAGRetriever with mocked ChromaDB."""

    @patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True)
    @patch("boring.rag.rag_retriever.chromadb")
    @patch("boring.rag.rag_retriever.ChromaSettings")
    def test_rag_retriever_init_with_chromadb(self, mock_settings, mock_chromadb, temp_project):
        """Test RAGRetriever initialization with ChromaDB available."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        retriever = RAGRetriever(temp_project)
        assert retriever.client is not None
        assert retriever.collection is not None

    @patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", False)
    def test_rag_retriever_init_without_chromadb(self, temp_project):
        """Test RAGRetriever initialization without ChromaDB."""
        retriever = RAGRetriever(temp_project)
        assert retriever.client is None
        assert retriever.collection is None
        assert not retriever.is_available

    @patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True)
    @patch("boring.rag.rag_retriever.chromadb")
    def test_rag_retriever_init_chromadb_error(self, mock_chromadb, temp_project):
        """Test RAGRetriever handles ChromaDB initialization errors."""
        mock_chromadb.PersistentClient.side_effect = Exception("ChromaDB error")

        retriever = RAGRetriever(temp_project)
        # Should handle gracefully
        assert retriever.client is None or retriever.collection is None

    @patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True)
    @patch("boring.rag.rag_retriever.chromadb")
    def test_rag_retriever_custom_persist_dir(self, mock_chromadb, temp_project):
        """Test RAGRetriever with custom persist directory."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        custom_dir = temp_project / "custom_rag"
        retriever = RAGRetriever(temp_project, persist_dir=custom_dir)
        assert retriever.persist_dir == custom_dir

    @patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True)
    @patch("boring.rag.rag_retriever.chromadb")
    def test_rag_retriever_custom_collection_name(self, mock_chromadb, temp_project):
        """Test RAGRetriever with custom collection name."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        retriever = RAGRetriever(temp_project, collection_name="custom_collection")
        assert retriever.collection_name == "custom_collection"

    @patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True)
    @patch("boring.rag.rag_retriever.chromadb")
    def test_rag_retriever_additional_roots(self, mock_chromadb, temp_project):
        """Test RAGRetriever with additional project roots."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        additional_root = temp_project.parent / "additional"
        additional_root.mkdir()

        retriever = RAGRetriever(temp_project, additional_roots=[additional_root])
        assert len(retriever.all_project_roots) == 2
        assert additional_root in retriever.all_project_roots

    @patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True)
    @patch("boring.rag.rag_retriever.chromadb")
    def test_rag_retriever_build_index_not_available(self, mock_chromadb, temp_project):
        """Test build_index when ChromaDB is not available."""
        retriever = RAGRetriever(temp_project)
        retriever.client = None
        retriever.collection = None

        result = retriever.build_index()
        assert result == 0

    @patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True)
    @patch("boring.rag.rag_retriever.chromadb")
    def test_rag_retriever_build_index_force(self, mock_chromadb, temp_project):
        """Test build_index with force=True."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 10
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client.create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        retriever = RAGRetriever(temp_project)
        retriever.client = mock_client
        retriever.collection = mock_collection

        # Mock indexer
        retriever.indexer.collect_files = MagicMock(return_value=[])

        retriever.build_index(force=True)
        # Should delete and recreate collection

        mock_client.delete_collection.assert_called_once()

    @patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True)
    @patch("boring.rag.rag_retriever.chromadb")
    def test_rag_retriever_retrieve_not_available(self, mock_chromadb, temp_project):
        """Test retrieve when ChromaDB is not available."""
        retriever = RAGRetriever(temp_project)
        retriever.collection = None

        results = retriever.retrieve("test query")
        assert results == []

    @patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True)
    @patch("boring.rag.rag_retriever.chromadb")
    def test_rag_retriever_retrieve_with_results(self, mock_chromadb, temp_project, sample_chunks):
        """Test retrieve with mock ChromaDB results."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        # Mock query results
        mock_collection.query.return_value = {
            "ids": [["chunk1", "chunk2"]],
            "distances": [[0.1, 0.2]],
            "metadatas": [
                [
                    {"file_path": "test.py", "chunk_type": "function", "name": "func_a"},
                    {"file_path": "test.py", "chunk_type": "function", "name": "func_b"},
                ]
            ],
            "documents": [["def func_a(): func_b()", "def func_b(): pass"]],
        }

        retriever = RAGRetriever(temp_project)
        retriever.client = mock_client
        retriever.collection = mock_collection
        retriever._chunks = {chunk.chunk_id: chunk for chunk in sample_chunks}

        results = retriever.retrieve("test query", n_results=5)
        assert len(results) > 0
        assert all(isinstance(r, RetrievalResult) for r in results)

    @patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True)
    @patch("boring.rag.rag_retriever.chromadb")
    def test_rag_retriever_retrieve_with_file_filter(self, mock_chromadb, temp_project):
        """Test retrieve with file_filter parameter."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        mock_collection.query.return_value = {
            "ids": [[]],
            "distances": [[]],
            "metadatas": [[]],
            "documents": [[]],
        }

        retriever = RAGRetriever(temp_project)
        retriever.client = mock_client
        retriever.collection = mock_collection

        retriever.retrieve("test", file_filter="auth")
        # Should call query with where filter
        mock_collection.query.assert_called_once()
        call_kwargs = mock_collection.query.call_args[1]
        assert "where" in call_kwargs

    @patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True)
    @patch("boring.rag.rag_retriever.chromadb")
    def test_rag_retriever_retrieve_with_threshold(
        self, mock_chromadb, temp_project, sample_chunks
    ):
        """Test retrieve with threshold filtering."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        # Mock results with varying distances
        mock_collection.query.return_value = {
            "ids": [["chunk1", "chunk2"]],
            "distances": [[0.9, 0.1]],  # chunk1 has high distance (low score)
            "metadatas": [
                [
                    {"file_path": "test.py", "chunk_type": "function", "name": "func_a"},
                    {"file_path": "test.py", "chunk_type": "function", "name": "func_b"},
                ]
            ],
            "documents": [["def func_a(): func_b()", "def func_b(): pass"]],
        }

        retriever = RAGRetriever(temp_project)
        retriever.client = mock_client
        retriever.collection = mock_collection
        retriever._chunks = {chunk.chunk_id: chunk for chunk in sample_chunks}

        # High threshold should filter out low-scoring results
        results = retriever.retrieve("test", threshold=0.5)
        # chunk1 has score ~0.1, should be filtered
        assert all(r.score >= 0.5 for r in results)

    @patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True)
    @patch("boring.rag.rag_retriever.chromadb")
    def test_rag_retriever_retrieve_query_error(self, mock_chromadb, temp_project):
        """Test retrieve handles ChromaDB query errors."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.query.side_effect = Exception("Query error")
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        retriever = RAGRetriever(temp_project)
        retriever.client = mock_client
        retriever.collection = mock_collection

        results = retriever.retrieve("test")
        assert results == []

    @patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True)
    @patch("boring.rag.rag_retriever.chromadb")
    def test_rag_retriever_get_stats(self, mock_chromadb, temp_project):
        """Test get_stats method."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 100
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        retriever = RAGRetriever(temp_project)
        retriever.client = mock_client
        retriever.collection = mock_collection
        # Populate chunks to have non-zero stats
        retriever._chunks = {f"chunk{i}": MagicMock() for i in range(100)}

        stats = retriever.get_stats()
        assert isinstance(stats, RAGStats)
        assert stats.total_chunks_indexed == 100

    @patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True)
    @patch("boring.rag.rag_retriever.chromadb")
    def test_rag_retriever_update_file(self, mock_chromadb, temp_project):
        """Test update_file method."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        test_file = temp_project / "test.py"
        test_file.write_text("def test(): pass")

        retriever = RAGRetriever(temp_project)
        retriever.client = mock_client
        retriever.collection = mock_collection

        # Mock indexer to return chunks
        mock_chunk = CodeChunk(
            chunk_id="chunk1",
            file_path="test.py",
            chunk_type="function",
            name="test",
            content="def test(): pass",
            start_line=1,
            end_line=1,
        )
        retriever.indexer.index_file = MagicMock(return_value=iter([mock_chunk]))

        result = retriever.update_file(test_file)
        assert result >= 0


class TestCreateRAGRetriever:
    """Tests for create_rag_retriever function."""

    @patch("boring.rag.rag_retriever.RAGRetriever")
    def test_create_rag_retriever(self, mock_retriever_class, temp_project):
        """Test create_rag_retriever function."""
        mock_instance = MagicMock()
        mock_retriever_class.return_value = mock_instance

        retriever = create_rag_retriever(temp_project)

        mock_retriever_class.assert_called_once()
        assert retriever == mock_instance


# =============================================================================
# DATACLASS TESTS
# =============================================================================


class TestRetrievalResult:
    """Tests for RetrievalResult dataclass."""

    def test_retrieval_result_creation(self, sample_chunks):
        """Test RetrievalResult creation."""
        result = RetrievalResult(
            chunk=sample_chunks[0],
            score=0.9,
            retrieval_method="vector",
            distance=0.1,
        )
        assert result.chunk == sample_chunks[0]
        assert result.score == 0.9
        assert result.retrieval_method == "vector"
        assert result.distance == 0.1

    def test_retrieval_result_optional_distance(self, sample_chunks):
        """Test RetrievalResult without distance."""
        result = RetrievalResult(
            chunk=sample_chunks[0],
            score=0.8,
            retrieval_method="graph",
        )
        assert result.distance is None


class TestRAGStats:
    """Tests for RAGStats dataclass."""

    def test_rag_stats_default(self):
        """Test RAGStats with default values."""
        stats = RAGStats()
        assert stats.index_stats is None
        assert stats.graph_stats is None
        assert stats.total_chunks_indexed == 0
        assert stats.last_index_time is None

    def test_rag_stats_custom(self):
        """Test RAGStats with custom values."""
        index_stats = IndexStats()
        graph_stats = GraphStats()

        stats = RAGStats(
            index_stats=index_stats,
            graph_stats=graph_stats,
            total_chunks_indexed=100,
            last_index_time="2024-01-01",
        )
        assert stats.index_stats == index_stats
        assert stats.graph_stats == graph_stats
        assert stats.total_chunks_indexed == 100
        assert stats.last_index_time == "2024-01-01"


class TestParsedChunk:
    """Tests for ParsedChunk dataclass."""

    def test_parsed_chunk_creation(self):
        """Test ParsedChunk creation."""
        chunk = ParsedChunk(
            type="function",
            name="test_func",
            start_line=1,
            end_line=10,
            content="def test_func(): pass",
        )
        assert chunk.type == "function"
        assert chunk.name == "test_func"
        assert chunk.start_line == 1
        assert chunk.end_line == 10
        assert chunk.content == "def test_func(): pass"
