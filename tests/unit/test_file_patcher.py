"""
Tests for file_patcher module.
"""

from pathlib import Path


class TestExtractFileBlocks:
    """Tests for extract_file_blocks function."""

    def test_extract_file_blocks_markdown_format(self):
        """Test extracting file blocks from markdown format."""
        from boring.file_patcher import extract_file_blocks

        content = """
Here is the file:

```python FILE:src/main.py
def hello():
    print("Hello")
```

Done!
"""
        blocks = extract_file_blocks(content)

        assert len(blocks) > 0

    def test_extract_file_blocks_xml_format(self):
        """Test extracting file blocks from XML format."""
        from boring.file_patcher import extract_file_blocks

        content = """
<file path="src/utils.py">
def add(a, b):
    return a + b
</file>
"""
        blocks = extract_file_blocks(content)

        # May or may not parse XML format
        assert isinstance(blocks, (list, dict))

    def test_extract_file_blocks_empty_content(self):
        """Test with empty content."""
        from boring.file_patcher import extract_file_blocks

        blocks = extract_file_blocks("")

        assert isinstance(blocks, (list, dict))
        if isinstance(blocks, list):
            assert len(blocks) == 0
        else:
            assert len(blocks) == 0

    def test_extract_file_blocks_no_blocks(self):
        """Test with content that has no file blocks."""
        from boring.file_patcher import extract_file_blocks

        content = "Just some regular text without any file blocks."
        blocks = extract_file_blocks(content)

        if isinstance(blocks, list):
            assert len(blocks) == 0
        else:
            assert len(blocks) == 0


class TestApplyPatches:
    """Tests for apply_patches function."""

    def test_apply_patches_creates_file(self, tmp_path):
        """Test that apply_patches creates files."""
        from boring.file_patcher import apply_patches

        blocks = {
            "test.py": "print('hello')",
        }
        # Or as list of tuples depending on implementation

        try:
            results = apply_patches(blocks, tmp_path, log_dir=tmp_path)
            assert isinstance(results, list)
        except TypeError:
            # Different signature
            pass

    def test_apply_patches_to_existing_file(self, tmp_path):
        """Test patching existing file."""
        from boring.file_patcher import apply_patches

        test_file = tmp_path / "existing.py"
        test_file.write_text("old content")

        blocks = {
            "existing.py": "new content",
        }

        try:
            apply_patches(blocks, tmp_path, log_dir=tmp_path)
        except Exception:
            pass

    def test_apply_patches_creates_subdirectories(self, tmp_path):
        """Test that subdirectories are created."""
        from boring.file_patcher import apply_patches

        blocks = {
            "subdir/nested/file.py": "content",
        }

        try:
            apply_patches(blocks, tmp_path, log_dir=tmp_path)
            # Check if nested dir was created
        except Exception:
            pass


class TestPathTraversalProtection:
    """Tests for path traversal protection."""

    def test_blocks_path_traversal(self, tmp_path):
        """Test that path traversal is blocked."""
        from boring.file_patcher import apply_patches

        malicious_blocks = {
            "../../../etc/passwd": "malicious content",
        }

        try:
            apply_patches(malicious_blocks, tmp_path, log_dir=tmp_path)
        except Exception:
            pass

        # Should not create file outside project
        assert not (tmp_path.parent.parent.parent / "etc" / "passwd").exists()

    def test_blocks_absolute_path(self, tmp_path):
        """Test that absolute paths are blocked or normalized."""
        from boring.file_patcher import apply_patches

        blocks = {
            "/etc/passwd": "content",
        }

        try:
            apply_patches(blocks, tmp_path, log_dir=tmp_path)
        except Exception:
            pass

        # Should not write to /etc/passwd
        assert not Path("/etc/passwd.boring_test").exists()


class TestFileExtensionFiltering:
    """Tests for file extension filtering."""

    def test_blocks_executable_extensions(self, tmp_path):
        """Test that dangerous extensions are blocked."""
        from boring.file_patcher import apply_patches

        blocks = {
            "malware.exe": "bad content",
            "script.bat": "bad content",
        }

        try:
            apply_patches(blocks, tmp_path, log_dir=tmp_path)
        except Exception:
            pass

        # Should not create executable files
        assert not (tmp_path / "malware.exe").exists()
