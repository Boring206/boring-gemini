import unittest.mock as mock
from pathlib import Path

from boring.rag.hyde import HyDEResult
from boring.rag.rag_retriever import RAGRetriever


class TestHybridRAGIntegration:
    @mock.patch("boring.rag.rag_retriever.get_hyde_expander")
    @mock.patch("boring.rag.rag_retriever.get_ensemble_reranker")
    @mock.patch(
        "boring.rag.rag_retriever.RAGRetriever.is_available", new_callable=mock.PropertyMock
    )
    def test_hybrid_rag_pipeline(self, mock_is_avail, mock_get_reranker, mock_get_hyde, tmp_path):
        # CORRECT ORDER: Bottom-most decorator first
        # mock_is_avail <- is_available (bottom)
        # mock_get_reranker <- get_ensemble_reranker (middle)
        # mock_get_hyde <- get_hyde_expander (top)

        mock_is_avail.return_value = True

        # Setup mocks
        mock_expander = mock.Mock()
        mock_expander.expand_query.return_value = HyDEResult(
            original_query="how to auth",
            hypothetical_document="How to authenticate in Python",
            hypothetical_code="def authenticate(user, pwd):",
            expanded_keywords=["auth", "login"],
            confidence=0.9,
        )
        mock_get_hyde.return_value = mock_expander

        mock_reranker = mock.Mock()
        mock_reranker.rerank.return_value = [(1, 0.95), (0, 0.85)]
        mock_get_reranker.return_value = mock_reranker

        # Mock ChromaDB and Collection
        mock_collection = mock.Mock()
        mock_collection.query.return_value = {
            "ids": [["id1", "id2"]],
            "distances": [[0.1, 0.2]],
            "metadatas": [
                [
                    {"file_path": "file1.py", "chunk_type": "function"},
                    {"file_path": "file2.py", "chunk_type": "function"},
                ]
            ],
            "documents": [["content1", "content2"]],
            "uris": [[None, None]],
            "data": [[None, None]],
        }
        mock_collection.count.return_value = 2

        # Initialize retriever with mocked collection
        with mock.patch("chromadb.PersistentClient"):
            retriever = RAGRetriever(project_root=Path(tmp_path))
            retriever.collection = mock_collection

            # Execute retrieval with Hybrid RAG enabled
            results = retriever.retrieve(
                query="how to auth", use_hyde=True, use_rerank=True, n_results=2
            )

            # Assertions
            mock_expander.expand_query.assert_called_once_with("how to auth")
            assert len(results) == 2
            assert results[0].chunk.file_path == "file2.py"
            assert results[0].score == 0.95

    @mock.patch("boring.rag.rag_retriever.get_hyde_expander")
    @mock.patch(
        "boring.rag.rag_retriever.RAGRetriever.is_available", new_callable=mock.PropertyMock
    )
    def test_retrieval_without_hyde(self, mock_is_avail, mock_get_hyde, tmp_path):
        # mock_is_avail <- is_available (bottom)
        # mock_get_hyde <- get_hyde_expander (top)
        mock_is_avail.return_value = True

        # Mock ChromaDB and Collection
        mock_collection = mock.Mock()
        mock_collection.query.return_value = {
            "ids": [["id1"]],
            "distances": [[0.1]],
            "metadatas": [[{"file_path": "file1.py", "chunk_type": "function"}]],
            "documents": [["content1"]],
            "uris": [[None]],
            "data": [[None]],
        }
        mock_collection.count.return_value = 1

        with mock.patch("chromadb.PersistentClient"):
            retriever = RAGRetriever(project_root=Path(tmp_path))
            retriever.collection = mock_collection
            retriever.retrieve(query="simple query", use_hyde=False, use_rerank=False)
            mock_get_hyde.assert_not_called()
