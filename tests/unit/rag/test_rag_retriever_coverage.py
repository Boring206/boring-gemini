import time
from unittest.mock import MagicMock, patch

import pytest

from boring.rag.code_indexer import CodeChunk
from boring.rag.rag_retriever import (
    RAGRetriever,
    RetrievalResult,
    _clear_query_cache,
    _get_intelligent_ranker,
    clear_session_context,
    get_session_context,
    set_session_context,
)


class TestRAGRetrieverUtility:
    def test_session_context(self):
        clear_session_context()
        assert get_session_context() is None

        set_session_context(task_type="debugging", focus_files=["file1.py"], keywords=["error"])
        ctx = get_session_context()
        assert ctx["task_type"] == "debugging"
        assert ctx["focus_files"] == ["file1.py"]
        assert ctx["keywords"] == ["error"]
        assert "set_at" in ctx

        clear_session_context()
        assert get_session_context() is None

    def test_get_intelligent_ranker_fallback(self, tmp_path):
        with patch("boring.intelligence.IntelligentRanker", side_effect=ImportError):
            ranker = _get_intelligent_ranker(tmp_path)
            assert ranker is None

    def test_clear_query_cache(self):
        from boring.rag.rag_retriever import _query_cache

        _query_cache["test"] = ([], time.time())
        _clear_query_cache()
        assert len(_query_cache) == 0


class TestRAGRetrieverCore:
    @pytest.fixture
    def mock_chroma(self):
        with patch("chromadb.PersistentClient") as mock_client:
            mock_collection = MagicMock()
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            yield mock_client, mock_collection

    @pytest.fixture
    def retriever(self, tmp_path, mock_chroma):
        with patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True):
            retriever = RAGRetriever(tmp_path)
            return retriever

    def test_init(self, tmp_path, mock_chroma):
        with patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True):
            retriever = RAGRetriever(tmp_path)
            assert retriever.project_root == tmp_path
            assert retriever.persist_dir == tmp_path / ".boring_memory" / "rag_db"
            assert retriever.is_available

    def test_build_index_empty(self, retriever, mock_chroma):
        mock_client, mock_collection = mock_chroma
        mock_collection.count.return_value = 0

        with patch.object(retriever.indexer, "collect_files", return_value=[]):
            with patch.object(retriever.index_state, "get_changed_files", return_value=[]):
                count = retriever.build_index()
                assert count == 0

    def test_retrieve_basic(self, retriever, mock_chroma):
        mock_client, mock_collection = mock_chroma

        # Mock ChromaDB results
        mock_collection.query.return_value = {
            "ids": [["chunk1"]],
            "distances": [[0.2]],
            "documents": [["def test(): pass"]],
            "metadatas": [
                [
                    {
                        "file_path": "test.py",
                        "name": "test",
                        "start_line": 1,
                        "end_line": 2,
                        "chunk_type": "function",
                    }
                ]
            ],
        }

        results = retriever.retrieve("unique_query", n_results=1)
        assert len(results) == 1
        assert results[0].chunk.chunk_id == "chunk1"
        # Similarity = 1.0 - 0.2 = 0.8
        # No keyword boost since 'unique_query' terms not in 'test' or content
        assert results[0].score == 0.8
        assert results[0].retrieval_method == "vector"

    def test_build_index_with_files(self, retriever, tmp_path, mock_chroma):
        mock_client, mock_collection = mock_chroma
        mock_collection.count.return_value = 0

        test_file = tmp_path / "app.py"
        test_file.write_text("def hello():\n    print('world')")

        with patch.object(retriever.indexer, "collect_files", return_value=[test_file]):
            with patch.object(retriever.index_state, "get_changed_files", return_value=[test_file]):
                _count = retriever.build_index()
                assert mock_collection.upsert.called

    def test_build_index_stale_files(self, retriever, mock_chroma):
        mock_client, mock_collection = mock_chroma

        # Mock stale state
        retriever.index_state.state = {"old.py": {"chunks": ["c1", "c2"]}}

        with patch.object(retriever.indexer, "collect_files", return_value=[]):
            with patch.object(retriever.index_state, "get_changed_files", return_value=[]):
                with patch.object(
                    retriever.index_state, "get_stale_files", return_value=["old.py"]
                ):
                    retriever.build_index()
                    mock_collection.delete.assert_called_with(ids=["c1", "c2"])
                    assert "old.py" not in retriever.index_state.state

    def test_build_index_force(self, retriever, mock_chroma):
        mock_client, mock_collection = mock_chroma

        retriever.build_index(force=True)
        # It's mock_client.return_value because retriever.client = chromadb.PersistentClient(...)
        mock_client.return_value.delete_collection.assert_called_once_with(
            retriever.collection_name
        )
        mock_client.return_value.create_collection.assert_called_once()

    def test_update_file(self, retriever, tmp_path, mock_chroma):
        mock_client, mock_collection = mock_chroma
        test_file = tmp_path / "hello.py"
        test_file.write_text("print('hello')")

        # Mock file in state
        retriever._file_to_chunks["hello.py"] = ["old1"]

        with patch.object(
            retriever.indexer,
            "index_file",
            return_value=[
                CodeChunk(
                    chunk_id="new1",
                    file_path="hello.py",
                    name="script",
                    content="print('hello')",
                    start_line=1,
                    end_line=1,
                    chunk_type="script",
                )
            ],
        ):
            count = retriever.update_file(test_file)
            assert count == 1
            mock_collection.delete.assert_called_with(ids=["old1"])
            mock_collection.upsert.assert_called()

    @pytest.mark.asyncio
    async def test_retrieve_async(self, retriever, mock_chroma):
        with patch.object(retriever, "retrieve", return_value=["result"]) as mock_ret:
            results = await retriever.retrieve_async("query")
            assert results == ["result"]
            mock_ret.assert_called_once()

    def test_retrieve_with_session_boost(self, retriever, mock_chroma):
        mock_client, mock_collection = mock_chroma

        set_session_context(task_type="debugging", focus_files=["test.py"])

        mock_collection.query.return_value = {
            "ids": [["chunk1"]],
            "distances": [[0.5]],
            "documents": [["def error_handler(): pass"]],
            "metadatas": [
                [
                    {
                        "file_path": "test.py",
                        "name": "error_handler",
                        "start_line": 1,
                        "end_line": 2,
                        "chunk_type": "function",
                    }
                ]
            ],
        }

        results = retriever.retrieve("error", n_results=1)
        clear_session_context()

        assert len(results) == 1
        # Base similarity: 0.5
        # Session boost: 0.2 (focus file) + 0.1 (debugging task match with 'error') = 0.3
        # Total score: 0.5 + 0.3 = 0.8
        # Plus keyword boost (0.15 for 'error' in name)
        assert results[0].score >= 0.8

    def test_get_modification_context(self, retriever):
        mock_graph = MagicMock()
        retriever.graph = mock_graph

        chunk = CodeChunk(
            chunk_id="c1",
            file_path="test.py",
            name="func",
            content="def func(): pass",
            start_line=1,
            end_line=2,
            chunk_type="function",
        )
        mock_graph.get_chunks_by_name.return_value = [chunk]
        mock_graph.get_context_for_modification.return_value = {
            "callers": [
                CodeChunk(
                    chunk_id="c2",
                    file_path="app.py",
                    name="main",
                    content="func()",
                    start_line=10,
                    end_line=11,
                    chunk_type="function",
                )
            ],
            "callees": [],
            "siblings": [],
        }

        context = retriever.get_modification_context("test.py", function_name="func")
        assert len(context["target"]) == 1
        assert len(context["callers"]) == 1
        assert context["target"][0].chunk.chunk_id == "c1"
        assert context["callers"][0].chunk.chunk_id == "c2"

    def test_smart_expand(self, retriever):
        mock_graph = MagicMock()
        retriever.graph = mock_graph

        chunk = CodeChunk(
            chunk_id="c1",
            file_path="test.py",
            name="func",
            content="def func(): pass",
            start_line=1,
            end_line=2,
            chunk_type="function",
        )
        mock_graph.get_chunk.return_value = chunk
        mock_graph.get_related_chunks.return_value = [
            CodeChunk(
                chunk_id="c3",
                file_path="util.py",
                name="helper",
                content="pass",
                start_line=1,
                end_line=2,
                chunk_type="function",
            )
        ]

        results = retriever.smart_expand("c1", depth=2)
        assert len(results) == 1
        assert results[0].chunk.chunk_id == "c3"
        assert results[0].retrieval_method == "smart_jump"

    def test_generate_context_injection(self, retriever, mock_chroma):
        # reuse retrieval logic
        with patch.object(retriever, "retrieve") as mock_retrieve:
            chunk = CodeChunk(
                chunk_id="c1",
                file_path="test.py",
                name="func",
                content="def func(): pass",
                start_line=1,
                end_line=2,
                chunk_type="function",
            )
            mock_retrieve.return_value = [
                RetrievalResult(chunk=chunk, score=0.9, retrieval_method="vector")
            ]

            context_str = retriever.generate_context_injection("my query")
            assert "Relevant Code Context" in context_str
            assert "test.py" in context_str
            assert "def func(): pass" in context_str

    def test_get_stats(self, retriever):
        stats = retriever.get_stats()
        assert isinstance(stats.total_chunks_indexed, int)
        assert stats.chroma_available is True

    def test_retrieve_caching(self, retriever, mock_chroma):
        mock_client, mock_collection = mock_chroma
        mock_collection.query.return_value = {"ids": [[]]}

        _clear_query_cache()

        # First call hits DB
        retriever.retrieve("unique query")
        assert mock_collection.query.call_count == 1

        # Second call hits cache
        retriever.retrieve("unique query")
        assert mock_collection.query.call_count == 1
