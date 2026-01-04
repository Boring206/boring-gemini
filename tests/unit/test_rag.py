"""
Unit tests for RAG system
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


class TestCodeIndexer:
    """Tests for CodeIndexer"""
    
    def test_code_chunk_creation(self):
        """Test CodeChunk dataclass"""
        from boring.rag.code_indexer import CodeChunk
        
        chunk = CodeChunk(
            chunk_id="abc123",
            file_path="test.py",
            chunk_type="function",
            name="my_func",
            content="def my_func(): pass",
            start_line=1,
            end_line=1
        )
        
        assert chunk.chunk_id == "abc123"
        assert chunk.chunk_type == "function"
        assert chunk.name == "my_func"
    
    def test_indexer_init(self, tmp_path):
        """Test indexer initialization"""
        from boring.rag.code_indexer import CodeIndexer
        
        indexer = CodeIndexer(tmp_path)
        assert indexer.project_root == tmp_path
    
    def test_indexer_parses_function(self, tmp_path):
        """Test indexer parses Python function"""
        from boring.rag.code_indexer import CodeIndexer
        
        # Create test file
        test_file = tmp_path / "test_module.py"
        test_file.write_text('''
def hello_world():
    """Say hello"""
    print("Hello!")
''')
        
        indexer = CodeIndexer(tmp_path)
        chunks = list(indexer.index_file(test_file))
        
        # Should have at least one function chunk
        func_chunks = [c for c in chunks if c.chunk_type == "function"]
        assert len(func_chunks) >= 1
        assert func_chunks[0].name == "hello_world"
    
    def test_indexer_parses_class(self, tmp_path):
        """Test indexer parses Python class"""
        from boring.rag.code_indexer import CodeIndexer
        
        test_file = tmp_path / "test_class.py"
        test_file.write_text('''
class MyClass:
    """A test class"""
    
    def method_one(self):
        pass
''')
        
        indexer = CodeIndexer(tmp_path)
        chunks = list(indexer.index_file(test_file))
        
        # Should have class chunk
        class_chunks = [c for c in chunks if c.chunk_type == "class"]
        assert len(class_chunks) >= 1
        assert class_chunks[0].name == "MyClass"


class TestDependencyGraph:
    """Tests for DependencyGraph"""
    
    def test_graph_build_empty(self):
        """Test graph with no chunks"""
        from boring.rag.graph_builder import DependencyGraph
        
        graph = DependencyGraph([])
        stats = graph.get_stats()
        assert stats.total_nodes == 0
    
    def test_graph_build_with_chunks(self):
        """Test graph with sample chunks"""
        from boring.rag.code_indexer import CodeChunk
        from boring.rag.graph_builder import DependencyGraph
        
        chunks = [
            CodeChunk(
                chunk_id="a",
                file_path="test.py",
                chunk_type="function",
                name="func_a",
                content="def func_a(): func_b()",
                start_line=1,
                end_line=1,
                dependencies=["func_b"]
            ),
            CodeChunk(
                chunk_id="b",
                file_path="test.py",
                chunk_type="function",
                name="func_b",
                content="def func_b(): pass",
                start_line=2,
                end_line=2,
                dependencies=[]
            )
        ]
        
        graph = DependencyGraph(chunks)
        
        # func_a calls func_b
        callees = graph.get_callees("a")
        assert len(callees) == 1
        assert callees[0].name == "func_b"
        
        # func_b is called by func_a
        callers = graph.get_callers("b")
        assert len(callers) == 1
        assert callers[0].name == "func_a"
    
    def test_impact_zone(self):
        """Test impact zone calculation"""
        from boring.rag.code_indexer import CodeChunk
        from boring.rag.graph_builder import DependencyGraph
        
        chunks = [
            CodeChunk("a", "test.py", "function", "caller", "def caller(): base()", 1, 1, ["base"]),
            CodeChunk("b", "test.py", "function", "base", "def base(): pass", 2, 2, []),
        ]
        
        graph = DependencyGraph(chunks)
        
        # Modifying "base" might break "caller"
        impact = graph.get_impact_zone("b")
        assert len(impact) == 1
        assert impact[0].name == "caller"


class TestRAGRetriever:
    """Tests for RAGRetriever"""
    
    @patch('boring.rag.rag_retriever.CHROMA_AVAILABLE', False)
    def test_retriever_without_chromadb(self, tmp_path):
        """Test retriever gracefully handles missing ChromaDB"""
        from boring.rag.rag_retriever import RAGRetriever
        
        retriever = RAGRetriever(tmp_path)
        assert not retriever.is_available
    
    def test_retriever_stats(self, tmp_path):
        """Test retriever stats"""
        from boring.rag.rag_retriever import RAGRetriever, RAGStats
        
        retriever = RAGRetriever(tmp_path)
        stats = retriever.get_stats()
        
        assert isinstance(stats, RAGStats)
        assert stats.total_chunks_indexed == 0
