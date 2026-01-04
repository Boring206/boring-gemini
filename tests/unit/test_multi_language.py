import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from boring.verification import CodeVerifier
from boring.rag.code_indexer import CodeIndexer, CodeChunk

class TestMultiLanguageVerification:
    def test_verify_syntax_node(self, tmp_path):
        js_file = tmp_path / "app.js"
        js_file.write_text("console.log('hello');")
        
        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        verifier.tools["node"] = True
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = verifier.verify_syntax(js_file)
            assert result.passed is True
            assert "node" in str(mock_run.call_args)

    def test_verify_syntax_go(self, tmp_path):
        go_file = tmp_path / "main.go"
        go_file.write_text("package main\nfunc main() {}")
        
        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        verifier.tools["go"] = True
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = verifier.verify_syntax(go_file)
            assert result.passed is True
            assert "go" in str(mock_run.call_args)

class TestMultiLanguageIndexing:
    def test_index_universal_js(self, tmp_path):
        js_file = tmp_path / "app.js"
        # Create a file with 60 lines to test chunking
        content = "\n".join([f"console.log({i});" for i in range(60)])
        js_file.write_text(content)
        
        indexer = CodeIndexer(project_root=tmp_path)
        chunks = list(indexer.index_file(js_file))
        
        # 60 lines with 50-line chunks and 5-line overlap
        # Chunk 1: 1-50
        # Chunk 2: 51-60
        assert len(chunks) == 2
        assert chunks[0].chunk_type == "code_block"
        assert chunks[0].file_path == "app.js"
        assert chunks[1].start_line == 51

    def test_index_project_multi_ext(self, tmp_path):
        (tmp_path / "app.js").write_text("console.log(1);")
        (tmp_path / "main.go").write_text("package main")
        (tmp_path / "README.md").write_text("# Title")
        
        indexer = CodeIndexer(project_root=tmp_path)
        chunks = list(indexer.index_project())
        
        paths = [c.file_path for c in chunks]
        assert "app.js" in paths
        assert "main.go" in paths
        assert "README.md" in paths
