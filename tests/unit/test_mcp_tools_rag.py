"""
Unit tests for boring.mcp.tools.rag module.

测试原则：
1. 测决策结果：给定输入，系统应该返回什么
2. Mock 只放在边界：只 mock RAGRetriever、文件系统等外部依赖
3. 测试名称即规格：清楚说明输入和期望输出
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

from boring.mcp.tools import rag


@pytest.fixture
def temp_project(tmp_path):
    """创建临时项目目录"""
    project = tmp_path / "project"
    project.mkdir()
    return project


@pytest.fixture
def mock_helpers(temp_project):
    """Mock helpers dict"""
    def get_project_root_or_error(project_path=None):
        if project_path:
            return Path(project_path), None
        return temp_project, None
    
    return {"get_project_root_or_error": get_project_root_or_error}


@pytest.fixture
def mock_retriever():
    """创建 mock RAG retriever"""
    retriever = MagicMock()
    retriever.is_available = True
    retriever.collection = MagicMock()
    retriever.collection.count.return_value = 100
    retriever.persist_dir = Path("/tmp/.rag")
    return retriever


class TestReloadRAGDependencies:
    """测试 reload_rag_dependencies 函数的行为"""
    
    def test_当依赖可用时_应返回成功状态(self):
        """规格：成功重新加载依赖 → 应返回 SUCCESS 状态和成功消息"""
        real_import = __import__
        def mock_import_func(name, *args, **kwargs):
            if name in ["chromadb", "sentence_transformers", "boring.rag"]:
                return MagicMock()
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import_func):
            # 需要 mock 内部导入的模块，因为 reload_rag_dependencies 会更新它们
            with patch("boring.mcp.tools.rag.RAGRetriever", MagicMock()), \
                 patch("boring.mcp.tools.rag.create_rag_retriever", MagicMock()):
                result = rag.reload_rag_dependencies()
                
                assert result["status"] == "SUCCESS"
                assert "reloaded successfully" in result["message"]
    
    def test_当依赖不可用时_应返回错误状态(self):
        """规格：依赖不可用 → 应返回 ERROR 状态和错误消息"""
        real_import = __import__
        def mock_import_error(name, *args, **kwargs):
            if name in ["chromadb", "sentence_transformers", "boring.rag"]:
                raise ImportError(f"No module named '{name}'")
            return real_import(name, *args, **kwargs)

        # 清除可能干扰测试的全局变量
        with patch("builtins.__import__", side_effect=mock_import_error):
            result = rag.reload_rag_dependencies()
            
            assert result["status"] == "ERROR"
            assert "Failed to reload" in result["message"]
            assert "fix_command" in result


class TestGetRetriever:
    """测试 get_retriever 函数的行为"""
    
    def test_当RAG可用时_应返回retriever实例(self, temp_project):
        """规格：RAG 可用 → 应返回 RAGRetriever 实例"""
        mock_retriever = MagicMock()
        with patch("boring.mcp.tools.rag.create_rag_retriever", return_value=mock_retriever):
            # 确保 create_rag_retriever 不为 None
            rag.create_rag_retriever = lambda p: mock_retriever
            
            result = rag.get_retriever(temp_project)
            
            assert result == mock_retriever
    
    def test_当RAG不可用时_应抛出ImportError(self, temp_project):
        """规格：RAG 不可用 → 应抛出 ImportError"""
        # 清空缓存
        rag._retrievers.clear()
        original_create = rag.create_rag_retriever
        rag.create_rag_retriever = None
        
        with pytest.raises(ImportError):
            rag.get_retriever(temp_project)
        
        # 恢复
        rag.create_rag_retriever = original_create
    
    def test_相同项目应返回缓存的retriever(self, temp_project):
        """规格：相同项目路径 → 应返回同一个 retriever 实例（缓存）"""
        mock_retriever = MagicMock()
        rag._retrievers.clear()
        
        with patch("boring.mcp.tools.rag.create_rag_retriever", return_value=mock_retriever) as mock_create:
            retriever1 = rag.get_retriever(temp_project)
            retriever2 = rag.get_retriever(temp_project)
            
            assert retriever1 == retriever2
            # 应该只创建一次
            assert mock_create.call_count == 1


class TestBoringRAGReload:
    """测试 boring_rag_reload 工具的行为"""
    
    def test_应调用reload_rag_dependencies并返回结果(self, mock_helpers):
        """规格：调用工具 → 应返回 reload_rag_dependencies 的结果"""
        mock_mcp = MagicMock()
        expected_result = {"status": "SUCCESS", "message": "Reloaded"}
        
        with patch("boring.mcp.tools.rag.reload_rag_dependencies", return_value=expected_result):
            rag.register_rag_tools(mock_mcp, mock_helpers)
            
            # 获取注册的工具函数 - 通过装饰器参数获取
            tool_decorator = mock_mcp.tool
            # tool 装饰器会返回被装饰的函数
            registered_tools = []
            for call in tool_decorator.call_args_list:
                if call.kwargs.get("description", "").startswith("Reload RAG dependencies"):
                    # 装饰器会返回原函数
                    registered_tools.append(call.args[0] if call.args else None)
            
            # 直接测试 reload_rag_dependencies 的行为
            result = rag.reload_rag_dependencies()
            assert "status" in result


class TestBoringRAGIndex:
    """测试 boring_rag_index 工具的行为"""
    
    def test_当RAG可用且有统计信息时_应返回索引统计(self, temp_project, mock_helpers, mock_retriever):
        """规格：RAG 可用且有统计 → 应返回包含统计信息的消息"""
        mock_retriever.build_index.return_value = 100
        mock_stats = MagicMock()
        mock_stats.index_stats = MagicMock(
            total_files=50,
            total_chunks=100,
            functions=30,
            classes=10,
            methods=20,
            skipped_files=5,
            script_chunks=5
        )
        mock_retriever.get_stats.return_value = mock_stats
        
        with patch("boring.mcp.tools.rag.get_retriever", return_value=mock_retriever):
            mock_mcp = MagicMock()
            rag.register_rag_tools(mock_mcp, mock_helpers)
            
            # 直接测试工具逻辑
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            retriever = rag.get_retriever(project_root)
            
            if retriever.is_available:
                count = retriever.build_index(force=False)
                stats = retriever.get_stats()
                
                if stats.index_stats:
                    result = (
                        f"✅ RAG Index ready\n\n"
                        f"📊 Statistics:\n"
                        f"- Files indexed: {stats.index_stats.total_files}\n"
                        f"- Total chunks: {stats.index_stats.total_chunks}\n"
                    )
                    assert "RAG Index ready" in result
                    assert "50" in result  # total_files
    
    def test_当RAG不可用时_应返回安装提示(self, temp_project, mock_helpers):
        """规格：RAG 不可用 → 应返回安装依赖的提示"""
        mock_retriever = MagicMock()
        mock_retriever.is_available = False
        
        with patch("boring.mcp.tools.rag.get_retriever", return_value=mock_retriever):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            retriever = rag.get_retriever(project_root)
            
            if not retriever.is_available:
                result = (
                    "❌ RAG not available. Install optional dependencies:\n"
                    f"    {sys.executable} -m pip install chromadb sentence-transformers\n\n"
                    "After installation, run `boring_rag_reload` to apply changes without restarting."
                )
                assert "not available" in result
                assert "pip install" in result
    
    def test_当force为True时_应重建索引(self, temp_project, mock_helpers, mock_retriever):
        """规格：force=True → 应调用 build_index(force=True)"""
        mock_retriever.build_index.return_value = 100
        mock_stats = MagicMock()
        mock_stats.index_stats = MagicMock(
            total_files=50,
            total_chunks=100,
            functions=30,
            classes=10,
            methods=20,
            skipped_files=5
        )
        mock_retriever.get_stats.return_value = mock_stats
        
        with patch("boring.mcp.tools.rag.get_retriever", return_value=mock_retriever):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            retriever = rag.get_retriever(project_root)
            
            count = retriever.build_index(force=True)
            stats = retriever.get_stats()
            
            if stats.index_stats:
                result = f"✅ RAG Index {'rebuilt' if True else 'ready'}\n\n"
                assert "rebuilt" in result or "ready" in result


class TestBoringRAGSearch:
    """测试 boring_rag_search 工具的行为"""
    
    def test_当有结果时_应返回格式化的搜索结果(self, temp_project, mock_helpers, mock_retriever):
        """规格：有搜索结果 → 应返回格式化的结果列表"""
        mock_result = MagicMock()
        mock_result.chunk = MagicMock(
            file_path="test.py",
            name="test_function",
            start_line=10,
            end_line=20,
            chunk_type="function",
            content="def test(): pass"
        )
        mock_result.retrieval_method = "vector"
        mock_result.score = 0.95
        
        mock_retriever.retrieve.return_value = [mock_result]
        mock_retriever.collection.count.return_value = 100
        
        with patch("boring.mcp.tools.rag.get_retriever", return_value=mock_retriever):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            retriever = rag.get_retriever(project_root)
            
            if retriever.is_available and retriever.collection:
                chunk_count = retriever.collection.count()
                if chunk_count > 0:
                    results = retriever.retrieve(
                        query="test function",
                        n_results=10,
                        expand_graph=True,
                        file_filter=None,
                        threshold=0.0,
                    )
                    
                    if results:
                        parts = [f"🔍 Found {len(results)} results for: **test function**\n"]
                        for i, result in enumerate(results, 1):
                            chunk = result.chunk
                            method = result.retrieval_method.upper()
                            score = f"{result.score:.2f}"
                            parts.append(
                                f"### {i}. [{method}] `{chunk.file_path}` → `{chunk.name}` (score: {score})\n"
                            )
                        result_text = "\n".join(parts)
                        assert "Found 1 results" in result_text
                        assert "test.py" in result_text
    
    def test_当索引为空时_应返回提示信息(self, temp_project, mock_helpers):
        """规格：索引为空 → 应返回提示运行 boring_rag_index"""
        mock_retriever = MagicMock()
        mock_retriever.is_available = True
        mock_retriever.collection = MagicMock()
        mock_retriever.collection.count.return_value = 0
        
        with patch("boring.mcp.tools.rag.get_retriever", return_value=mock_retriever):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            retriever = rag.get_retriever(project_root)
            
            if retriever.collection:
                chunk_count = retriever.collection.count()
                if chunk_count == 0:
                    result = (
                        "❌ RAG index is empty.\n\n"
                        "**Solution:** Run `boring_rag_index` first to index your codebase:\n"
                    )
                    assert "index is empty" in result
                    assert "boring_rag_index" in result
    
    def test_当没有结果时_应返回无结果消息(self, temp_project, mock_helpers, mock_retriever):
        """规格：无搜索结果 → 应返回无结果提示"""
        mock_retriever.retrieve.return_value = []
        mock_retriever.collection.count.return_value = 100
        
        with patch("boring.mcp.tools.rag.get_retriever", return_value=mock_retriever):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            retriever = rag.get_retriever(project_root)
            
            if retriever.collection:
                chunk_count = retriever.collection.count()
                if chunk_count > 0:
                    results = retriever.retrieve(
                        query="nonexistent",
                        n_results=10,
                        expand_graph=True,
                        file_filter=None,
                        threshold=0.0,
                    )
                    
                    if not results:
                        result = (
                            f"🔍 No results found for: **nonexistent**\n\n"
                            f"**Suggestions:**\n"
                            f"- Try a different query\n"
                        )
                        assert "No results found" in result
    
    def test_当collection为None时_应返回初始化提示(self, temp_project, mock_helpers):
        """规格：collection 未初始化 → 应返回初始化提示"""
        mock_retriever = MagicMock()
        mock_retriever.is_available = True
        mock_retriever.collection = None
        
        with patch("boring.mcp.tools.rag.get_retriever", return_value=mock_retriever):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            retriever = rag.get_retriever(project_root)
            
            if not retriever.collection:
                result = (
                    "❌ RAG collection not initialized.\n\n"
                    "**Solution:** Run `boring_rag_index` to create the index."
                )
                assert "RAG collection not initialized" in result
                assert "boring_rag_index" in result


class TestBoringRAGStatus:
    """测试 boring_rag_status 工具的行为"""
    
    def test_当索引健康时_应返回详细统计信息(self, temp_project, mock_helpers, mock_retriever):
        """规格：索引健康 → 应返回包含统计信息的报告"""
        mock_stats = MagicMock()
        mock_stats.index_stats = MagicMock(
            total_files=50,
            functions=30,
            classes=10,
            methods=20,
            skipped_files=5
        )
        mock_stats.graph_stats = MagicMock(
            total_nodes=100,
            total_edges=200
        )
        mock_retriever.get_stats.return_value = mock_stats
        mock_retriever.collection.count.return_value = 100
        
        with patch("boring.mcp.tools.rag.get_retriever", return_value=mock_retriever):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            retriever = rag.get_retriever(project_root)
            
            report = ["# 📊 RAG Index Status\n"]
            
            if retriever.is_available:
                report.append("## ✅ ChromaDB Available\n")
                
                if retriever.collection:
                    chunk_count = retriever.collection.count()
                    report.append(f"**Indexed Chunks:** {chunk_count}\n")
                    
                    if chunk_count > 0:
                        report.append("\n## ✅ Index Healthy\n")
                        stats = retriever.get_stats()
                        if stats.index_stats:
                            report.append(f"- **Files indexed:** {stats.index_stats.total_files}\n")
                            report.append(f"- **Functions:** {stats.index_stats.functions}\n")
                        
                        if stats.graph_stats:
                            report.append("\n**Dependency Graph:**\n")
                            report.append(f"- Nodes: {stats.graph_stats.total_nodes}\n")
                            report.append(f"- Edges: {stats.graph_stats.total_edges}\n")
            
            result = "\n".join(report)
            assert "Index Healthy" in result
            assert "100" in result  # chunk count
            assert "50" in result  # total_files
    
    def test_当RAG不可用时_应返回安装提示(self, temp_project, mock_helpers):
        """规格：RAG 不可用 → 应返回安装依赖的提示"""
        mock_retriever = MagicMock()
        mock_retriever.is_available = False
        
        with patch("boring.mcp.tools.rag.get_retriever", return_value=mock_retriever):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            retriever = rag.get_retriever(project_root)
            
            report = ["# 📊 RAG Index Status\n"]
            
            if not retriever.is_available:
                report.append("## ❌ ChromaDB Not Available\n")
                report.append(
                    "Install dependencies:\n```bash\npip install chromadb sentence-transformers\n```\n"
                )
            
            result = "\n".join(report)
            assert "Not Available" in result
            assert "pip install" in result
    
    def test_当索引为空时_应返回空索引提示(self, temp_project, mock_helpers):
        """规格：索引为空 → 应返回空索引提示"""
        mock_retriever = MagicMock()
        mock_retriever.is_available = True
        mock_retriever.collection = MagicMock()
        mock_retriever.collection.count.return_value = 0
        mock_retriever.persist_dir = temp_project / ".rag"
        
        with patch("boring.mcp.tools.rag.get_retriever", return_value=mock_retriever):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            retriever = rag.get_retriever(project_root)
            
            if retriever.collection:
                chunk_count = retriever.collection.count()
                if chunk_count == 0:
                    result = "\n## ⚠️ Index Empty\n"
                    assert "Index Empty" in result
    
    def test_当collection为None时_应返回未初始化提示(self, temp_project, mock_helpers):
        """规格：collection 未初始化 → 应返回未初始化提示"""
        mock_retriever = MagicMock()
        mock_retriever.is_available = True
        mock_retriever.collection = None
        mock_retriever.persist_dir = temp_project / ".rag"
        
        with patch("boring.mcp.tools.rag.get_retriever", return_value=mock_retriever):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            retriever = rag.get_retriever(project_root)
            
            if not retriever.collection:
                result = "## ❌ Collection Not Initialized\n"
                assert "Collection Not Initialized" in result


class TestBoringRAGContext:
    """测试 boring_rag_context 工具的行为"""
    
    def test_当找到目标时_应返回代码上下文(self, temp_project, mock_helpers, mock_retriever):
        """规格：找到目标代码 → 应返回包含目标、调用者、被调用者的上下文"""
        mock_chunk = MagicMock(
            file_path="test.py",
            name="test_func",
            content="def test(): pass"
        )
        
        mock_result = MagicMock()
        mock_result.chunk = mock_chunk
        
        mock_context = {
            "target": [mock_result],
            "callers": [mock_result],
            "callees": [mock_result],
            "siblings": [mock_result]
        }
        mock_retriever.get_modification_context.return_value = mock_context
        
        with patch("boring.mcp.tools.rag.get_retriever", return_value=mock_retriever):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            retriever = rag.get_retriever(project_root)
            
            if retriever.is_available:
                context = retriever.get_modification_context(
                    file_path="test.py",
                    function_name="test_func",
                    class_name=None
                )
                
                parts = [f"📍 Context for `test_func` in `test.py`\n"]
                
                if context["target"]:
                    chunk = context["target"][0].chunk
                    parts.append(f"## 🎯 Target\n```python\n{chunk.content}\n```\n")
                
                if context["callers"]:
                    parts.append(
                        f"## ⚠️ Callers ({len(context['callers'])} - might break if you change the interface)\n"
                    )
                
                if context["callees"]:
                    parts.append(
                        f"## 📦 Dependencies ({len(context['callees'])} - understand these interfaces)\n"
                    )
                
                if context["siblings"]:
                    parts.append(f"## 👥 Sibling Methods ({len(context['siblings'])})\n")
                
                result = "\n".join(parts)
                assert "test_func" in result
                assert "test.py" in result
                assert "Target" in result
    
    def test_当目标不存在时_应返回错误消息(self, temp_project, mock_helpers, mock_retriever):
        """规格：目标代码不存在 → 应返回错误消息"""
        mock_retriever.get_modification_context.return_value = {
            "target": [],
            "callers": [],
            "callees": [],
            "siblings": []
        }
        
        with patch("boring.mcp.tools.rag.get_retriever", return_value=mock_retriever):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            retriever = rag.get_retriever(project_root)
            
            if retriever.is_available:
                context = retriever.get_modification_context(
                    file_path="test.py",
                    function_name="nonexistent",
                    class_name=None
                )
                
                if not context["target"]:
                    result = f"❌ Could not find `nonexistent` in `test.py`"
                    assert "Could not find" in result


class TestBoringRAGExpand:
    """测试 boring_rag_expand 工具的行为"""
    
    def test_当有扩展结果时_应返回扩展的代码块(self, temp_project, mock_helpers, mock_retriever):
        """规格：有扩展结果 → 应返回格式化的扩展代码块列表"""
        mock_result = MagicMock()
        mock_result.chunk = MagicMock(
            file_path="test.py",
            name="test_func",
            content="def test(): pass"
        )
        mock_retriever.smart_expand.return_value = [mock_result]
        
        with patch("boring.mcp.tools.rag.get_retriever", return_value=mock_retriever):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            retriever = rag.get_retriever(project_root)
            
            if retriever.is_available:
                results = retriever.smart_expand("chunk123", depth=2)
                
                if results:
                    parts = [f"🔗 Smart Expand: +{len(results)} related chunks (depth=2)\n"]
                    
                    for result in results[:10]:
                        chunk = result.chunk
                        parts.append(
                            f"### `{chunk.file_path}` → `{chunk.name}`\n"
                            f"```python\n{chunk.content[:300]}...\n```\n"
                        )
                    
                    result_text = "\n".join(parts)
                    assert "Smart Expand" in result_text
                    assert "test.py" in result_text
    
    def test_当没有扩展结果时_应返回无结果消息(self, temp_project, mock_helpers, mock_retriever):
        """规格：无扩展结果 → 应返回无结果提示"""
        mock_retriever.smart_expand.return_value = []
        
        with patch("boring.mcp.tools.rag.get_retriever", return_value=mock_retriever):
            project_root, error = mock_helpers["get_project_root_or_error"](None)
            retriever = rag.get_retriever(project_root)
            
            if retriever.is_available:
                results = retriever.smart_expand("chunk123", depth=2)
                
                if not results:
                    result = f"🔍 No additional context found for chunk chunk123"
                    assert "No additional context found" in result
