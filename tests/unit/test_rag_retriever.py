"""
Unit tests for boring.rag.rag_retriever module.

测试原则：
1. 测试决策结果：给定查询，应该返回什么结果
2. 只 mock 边界：ChromaDB 是外部数据库，可以 mock
3. 测试名称即规格：清楚说明输入和期望输出
"""

from unittest.mock import MagicMock, patch

import pytest

from boring.rag.rag_retriever import (
    RAGRetriever,
    RAGStats,
    RetrievalResult,
)


@pytest.fixture
def temp_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "test.py").write_text("def test(): pass\n", encoding="utf-8")
    return project


class TestRAGRetrieverInitialization:
    """测试 RAGRetriever 初始化的行为"""

    def test_當ChromaDB可用時_應初始化成功並可检索(self, temp_project):
        """規格：ChromaDB 可用 → is_available 应为 True，可以执行检索"""
        with (
            patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True),
            patch("boring.rag.rag_retriever.chromadb") as mock_chromadb,
        ):
            mock_client = MagicMock()
            mock_collection = MagicMock()
            mock_client.get_or_create_collection.return_value = mock_collection
            mock_chromadb.PersistentClient.return_value = mock_client

            with patch("boring.rag.rag_retriever.ChromaSettings"):
                retriever = RAGRetriever(temp_project)

                # 测试结果：应该可以检索
                assert retriever.is_available is True
                assert retriever.project_root == temp_project

    def test_當ChromaDB不可用時_應标记為不可用(self, temp_project):
        """規格：ChromaDB 不可用 → is_available 应为 False"""
        with patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", False):
            retriever = RAGRetriever(temp_project)

            # 测试结果：应该标记为不可用
            assert retriever.is_available is False

    def test_當ChromaDB初始化失敗時_應優雅降級為不可用(self, temp_project):
        """規格：ChromaDB 初始化失败 → 应优雅降级，is_available 为 False"""
        with (
            patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True),
            patch("boring.rag.rag_retriever.chromadb") as mock_chromadb,
        ):
            # Mock 数据库初始化失败（边界错误）
            mock_chromadb.PersistentClient.side_effect = Exception("DB Error")

            retriever = RAGRetriever(temp_project)

            # 测试结果：应该优雅降级
            assert retriever.is_available is False

    def test_init_with_additional_roots(self, temp_project):
        """Test initialization with additional project roots."""
        additional = temp_project.parent / "additional"
        additional.mkdir()

        with patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", False):
            retriever = RAGRetriever(temp_project, additional_roots=[additional])

            assert len(retriever.all_project_roots) == 2
            assert additional in retriever.all_project_roots

    def test_is_available_property(self, temp_project):
        """Test is_available property."""
        with (
            patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True),
            patch("boring.rag.rag_retriever.chromadb") as mock_chromadb,
        ):
            mock_client = MagicMock()
            mock_collection = MagicMock()
            mock_client.get_or_create_collection.return_value = mock_collection
            mock_chromadb.PersistentClient.return_value = mock_client

            with patch("boring.rag.rag_retriever.ChromaSettings"):
                retriever = RAGRetriever(temp_project)

                assert retriever.is_available is True

                # Test when collection is None
                retriever.collection = None
                assert retriever.is_available is False

    def test_當RAG不可用時_構築索引應返回0(self, temp_project):
        """規格：is_available=False → build_index() 应返回 0（不执行索引）"""
        with patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", False):
            retriever = RAGRetriever(temp_project)

            result = retriever.build_index()

            # 测试结果：应该返回 0，表示没有索引任何内容
            assert result == 0

    def test_當強制重建索引時_應清除舊索引並重建(self, temp_project):
        """規格：build_index(force=True) → 应清除旧索引，返回新索引的chunk数量"""
        with (
            patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True),
            patch("boring.rag.rag_retriever.chromadb") as mock_chromadb,
            patch("boring.rag.rag_retriever.CodeIndexer") as mock_indexer_class,
            patch("boring.rag.rag_retriever.IndexState") as mock_state_class,
        ):
            # Mock 外部数据库（边界）
            mock_client = MagicMock()
            mock_collection = MagicMock()
            mock_collection.count.return_value = 5  # 新索引后的数量
            mock_client.get_or_create_collection.return_value = mock_collection
            mock_client.delete_collection.return_value = None
            mock_client.create_collection.return_value = mock_collection
            mock_chromadb.PersistentClient.return_value = mock_client

            # Mock 文件系统操作（边界）
            mock_indexer = MagicMock()
            mock_indexer.collect_files.return_value = []
            mock_indexer.index_file.return_value = []
            mock_indexer.stats = MagicMock()
            mock_indexer_class.return_value = mock_indexer

            mock_state = MagicMock()
            mock_state.get_changed_files.return_value = []
            mock_state.get_stale_files.return_value = []
            mock_state_class.return_value = mock_state

            retriever = RAGRetriever(temp_project)

            result = retriever.build_index(force=True)

            # 测试结果：应该返回索引的chunk数量
            assert result == 5

    def test_當RAG不可用時_檢索應返回空列表(self, temp_project):
        """規格：is_available=False → retrieve(query) 应返回空列表"""
        with patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", False):
            retriever = RAGRetriever(temp_project)

            results = retriever.retrieve("test query")

            # 测试结果：应该返回空列表
            assert results == []

    def test_當查詢代碼時_應返回相關的代码塊(self, temp_project):
        """規格：retrieve("test function") → 应返回包含相关代码的 RetrievalResult 列表"""
        with (
            patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True),
            patch("boring.rag.rag_retriever.chromadb") as mock_chromadb,
        ):
            # Mock 外部数据库查询（边界）
            mock_client = MagicMock()
            mock_collection = MagicMock()
            mock_collection.query.return_value = {
                "ids": [["chunk1", "chunk2"]],
                "distances": [[0.1, 0.2]],
                "metadatas": [
                    [
                        {"file_path": "test.py", "name": "test"},
                        {"file_path": "test2.py", "name": "test2"},
                    ]
                ],
                "documents": [["def test(): pass", "def test2(): pass"]],
            }
            mock_client.get_or_create_collection.return_value = mock_collection
            mock_chromadb.PersistentClient.return_value = mock_client

            retriever = RAGRetriever(temp_project)
            # 设置内部状态（不 mock 自己的 domain logic）
            retriever._chunks = {
                "chunk1": MagicMock(file_path="test.py", name="test", content="def test(): pass"),
                "chunk2": MagicMock(
                    file_path="test2.py", name="test2", content="def test2(): pass"
                ),
            }

            results = retriever.retrieve("test query", n_results=5)

            # 测试结果：应该返回检索结果列表
            assert len(results) > 0
            assert all(isinstance(r, RetrievalResult) for r in results)
            # 每个结果应该有 chunk 和 score
            assert all(hasattr(r, "chunk") and hasattr(r, "score") for r in results)

    def test_當設置閾值時_應只返回分數高於閾值的結果(self, temp_project):
        """規格：retrieve(query, threshold=0.5) → 应只返回 score >= 0.5 的结果"""
        with (
            patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True),
            patch("boring.rag.rag_retriever.chromadb") as mock_chromadb,
        ):
            # Mock 数据库返回不同分数的结果
            mock_client = MagicMock()
            mock_collection = MagicMock()
            mock_collection.query.return_value = {
                "ids": [["chunk1", "chunk2"]],
                "distances": [[0.1, 0.9]],  # chunk2 分数低（距离大）
                "metadatas": [[{"file_path": "test.py"}, {"file_path": "test2.py"}]],
                "documents": [["def test(): pass", "def test2(): pass"]],
            }
            mock_client.get_or_create_collection.return_value = mock_collection
            mock_chromadb.PersistentClient.return_value = mock_client

            retriever = RAGRetriever(temp_project)
            retriever._chunks = {
                "chunk1": MagicMock(file_path="test.py", name="test", content="def test(): pass"),
                "chunk2": MagicMock(
                    file_path="test2.py", name="test2", content="def test2(): pass"
                ),
            }

            results = retriever.retrieve("test query", threshold=0.5)

            # 测试结果：应该过滤掉低分结果
            assert len(results) <= 1
            if results:
                assert results[0].score >= 0.5

    def test_retrieve_with_file_filter(self, temp_project):
        """Test retrieve with file_filter."""
        with (
            patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True),
            patch("boring.rag.rag_retriever.chromadb") as mock_chromadb,
        ):
            mock_client = MagicMock()
            mock_collection = MagicMock()
            mock_collection.query.return_value = {
                "ids": [["chunk1"]],
                "distances": [[0.1]],
                "metadatas": [[{"file_path": "auth/test.py"}]],
                "documents": [["def test(): pass"]],
            }
            mock_client.get_or_create_collection.return_value = mock_collection
            mock_chromadb.PersistentClient.return_value = mock_client

            retriever = RAGRetriever(temp_project)
            retriever._chunks = {
                "chunk1": MagicMock(
                    file_path="auth/test.py", name="test", content="def test(): pass"
                )
            }

            retriever.retrieve("test", file_filter="auth")

            # Should call query with where filter
            call_kwargs = mock_collection.query.call_args[1]
            assert "where" in call_kwargs

    def test_retrieve_query_failure(self, temp_project):
        """Test retrieve when query fails."""
        with (
            patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True),
            patch("boring.rag.rag_retriever.chromadb") as mock_chromadb,
        ):
            mock_client = MagicMock()
            mock_collection = MagicMock()
            mock_collection.query.side_effect = Exception("Query error")
            mock_client.get_or_create_collection.return_value = mock_collection
            mock_chromadb.PersistentClient.return_value = mock_client

            retriever = RAGRetriever(temp_project)

            results = retriever.retrieve("test query")

            assert results == []

    def test_當沒有依賴圖時_獲取修改上下文應返回空結果(self, temp_project):
        """規格：graph=None → get_modification_context() 应返回空的上下文字典"""
        with patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", False):
            retriever = RAGRetriever(temp_project)
            retriever.graph = None

            context = retriever.get_modification_context("test.py", function_name="test")

            # 测试结果：应该返回空上下文
            assert context == {"target": [], "callers": [], "callees": [], "siblings": []}

    def test_當未指定函數或類名時_獲取修改上下文應返回空結果(self, temp_project):
        """規格：function_name=None, class_name=None → 应返回空上下文"""
        with patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", False):
            retriever = RAGRetriever(temp_project)
            retriever.graph = MagicMock()

            context = retriever.get_modification_context("test.py")

            # 测试结果：没有目标名称，应该返回空上下文
            assert context == {"target": [], "callers": [], "callees": [], "siblings": []}

    def test_smart_expand_no_graph(self, temp_project):
        """Test smart_expand when graph is None."""
        with patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", False):
            retriever = RAGRetriever(temp_project)
            retriever.graph = None

            results = retriever.smart_expand("chunk1")

            assert results == []

    def test_smart_expand_chunk_not_found(self, temp_project):
        """Test smart_expand when chunk not found."""
        with patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", False):
            retriever = RAGRetriever(temp_project)
            mock_graph = MagicMock()
            mock_graph.get_chunk.return_value = None
            retriever.graph = mock_graph

            results = retriever.smart_expand("nonexistent")

            assert results == []

    def test_當獲取統計信息時_應返回包含索引數量的RAGStats(self, temp_project):
        """規格：get_stats() → 应返回包含 total_chunks_indexed 的 RAGStats"""
        with patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", False):
            retriever = RAGRetriever(temp_project)
            retriever._chunks = {"chunk1": MagicMock(), "chunk2": MagicMock()}

            stats = retriever.get_stats()

            # 测试结果：应该返回统计信息
            assert isinstance(stats, RAGStats)
            assert stats.total_chunks_indexed == 2

    def test_當清除索引時_應清空所有數據和數據庫集合(self, temp_project):
        """規格：clear() → 应清空内存中的chunks、文件映射和数据库集合"""
        with (
            patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", True),
            patch("boring.rag.rag_retriever.chromadb") as mock_chromadb,
        ):
            # Mock 外部数据库（边界）
            mock_client = MagicMock()
            mock_collection = MagicMock()
            mock_client.get_or_create_collection.return_value = mock_collection
            mock_client.delete_collection.return_value = None
            mock_client.create_collection.return_value = mock_collection
            mock_chromadb.PersistentClient.return_value = mock_client

            retriever = RAGRetriever(temp_project)
            retriever._chunks = {"chunk1": MagicMock()}
            retriever._file_to_chunks = {"test.py": ["chunk1"]}
            retriever.graph = MagicMock()

            retriever.clear()

            # 测试结果：应该清空所有数据
            assert len(retriever._chunks) == 0
            assert len(retriever._file_to_chunks) == 0
            assert retriever.graph is None

    def test_update_file_not_available(self, temp_project):
        """Test update_file when RAG not available."""
        with patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", False):
            retriever = RAGRetriever(temp_project)

            result = retriever.update_file(temp_project / "test.py")

            assert result == 0

    def test_generate_context_injection_no_results(self, temp_project):
        """Test generate_context_injection when no results."""
        with patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", False):
            retriever = RAGRetriever(temp_project)

            context = retriever.generate_context_injection("test query")

            assert context == ""

    @pytest.mark.asyncio
    async def test_retrieve_async(self, temp_project):
        """Test retrieve_async method."""
        with patch("boring.rag.rag_retriever.CHROMA_AVAILABLE", False):
            retriever = RAGRetriever(temp_project)

            # Mock the sync retrieve method
            with patch.object(retriever, "retrieve", return_value=[]):
                results = await retriever.retrieve_async("test query")

                assert results == []
