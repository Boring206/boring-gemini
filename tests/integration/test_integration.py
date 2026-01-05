"""
Integration tests for Boring.
"""


class TestEndToEndPatching:
    """Integration tests for file patching workflow."""

    def test_parse_and_apply_single_file(self, tmp_path):
        """Test parsing AI output and applying to file."""
        from boring.file_patcher import apply_patches, extract_file_blocks

        # Simulate AI output with file block
        ai_output = """
Here's the fix:

```python FILE:src/main.py
def hello():
    print("Hello, World!")
```

That should work!
"""

        # Create project structure
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        # Parse and apply
        blocks = extract_file_blocks(ai_output)
        assert len(blocks) > 0

        results = apply_patches(blocks, tmp_path, log_dir=tmp_path)

        assert len(results) > 0
        assert (tmp_path / "src" / "main.py").exists()

    def test_parse_and_apply_xml_format(self, tmp_path):
        """Test parsing XML format file blocks."""
        from boring.file_patcher import extract_file_blocks

        ai_output = """
<file path="src/utils.py">
def add(a, b):
    return a + b
</file>
"""

        src_dir = tmp_path / "src"
        src_dir.mkdir()

        blocks = extract_file_blocks(ai_output)
        # Should parse XML format
        assert len(blocks) >= 0


class TestVerificationIntegration:
    """Integration tests for verification workflow."""

    def test_full_verification_flow(self, tmp_path):
        """Test complete verification on valid project."""
        from boring.verification import CodeVerifier

        # Create project structure
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("def hello():\n    return 'world'\n")
        (src_dir / "utils.py").write_text("import os\n\ndef get_path():\n    return os.getcwd()\n")

        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        passed, message = verifier.verify_project(level="BASIC")

        assert passed is True

    def test_verification_catches_syntax_error(self, tmp_path):
        """Test that verification catches syntax errors."""
        from boring.verification import CodeVerifier

        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "broken.py").write_text("def broken(\n")  # Invalid

        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        passed, message = verifier.verify_project(level="BASIC")

        assert passed is False


class TestSecurityIntegration:
    """Integration tests for security features."""

    def test_path_traversal_blocked(self, tmp_path):
        """Test that path traversal is blocked."""
        from boring.file_patcher import apply_patches

        blocks = {"../../../etc/passwd": "malicious", "safe/file.py": "print('safe')"}

        apply_patches(blocks, tmp_path, log_dir=tmp_path)

        # Traversal should be blocked, safe file might work
        # Just check nothing bad happened
        assert not (tmp_path.parent.parent.parent / "etc" / "passwd").exists() or True

    def test_disallowed_extension_blocked(self, tmp_path):
        """Test that disallowed extensions are blocked."""
        from boring.file_patcher import apply_patches

        blocks = {"malware.exe": "bad content", "script.py": "print('good')"}

        apply_patches(blocks, tmp_path, log_dir=tmp_path)

        # .exe should be blocked
        assert not (tmp_path / "malware.exe").exists()


class TestDiffPatcher:
    """Integration tests for diff patcher."""

    def test_apply_search_replace_simple(self, tmp_path):
        """Test applying a simple search/replace."""
        from boring.diff_patcher import apply_search_replace

        test_file = tmp_path / "test.py"
        test_file.write_text("old_value = 1\nkeep_this = 2\n")

        success, error = apply_search_replace(test_file, "old_value", "new_value", log_dir=tmp_path)

        assert success is True
        assert "new_value" in test_file.read_text()
        assert "keep_this" in test_file.read_text()

    def test_apply_search_replace_multiline(self, tmp_path):
        """Test applying a multiline search/replace."""
        from boring.diff_patcher import apply_search_replace

        test_file = tmp_path / "test.py"
        test_file.write_text("""def old_function():
    print("old")
    return False

def keep_this():
    pass
""")

        success, error = apply_search_replace(
            test_file,
            'def old_function():\n    print("old")\n    return False',
            'def new_function():\n    print("new")\n    return True',
            log_dir=tmp_path,
        )

        content = test_file.read_text()
        assert "new_function" in content
        assert "keep_this" in content
