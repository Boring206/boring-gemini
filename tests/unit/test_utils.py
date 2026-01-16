"""
Tests for boring.utils module.
"""

from boring.utils import get_project_tree, robust_read_file, robust_write_file


class TestRobustFileOperations:
    """Tests for robust file operations."""

    def test_robust_write_file(self, tmp_path):
        """Test robust file writing."""
        test_file = tmp_path / "test.txt"
        content = "Hello, World!"

        robust_write_file(test_file, content)

        assert test_file.exists()
        assert test_file.read_text(encoding="utf-8") == content

    def test_robust_read_file(self, tmp_path):
        """Test robust file reading."""
        test_file = tmp_path / "test.txt"
        content = "Test content"
        test_file.write_text(content, encoding="utf-8")

        result = robust_read_file(test_file)

        assert result == content

    def test_robust_write_file_creates_parents(self, tmp_path):
        """Test that robust_write_file creates parent directories."""
        test_file = tmp_path / "subdir" / "nested" / "test.txt"
        content = "Nested content"

        # Create parent directories first
        test_file.parent.mkdir(parents=True, exist_ok=True)

        robust_write_file(test_file, content)

        assert test_file.exists()
        assert test_file.read_text(encoding="utf-8") == content


class TestGetProjectTree:
    """Tests for get_project_tree function."""

    def test_basic_tree(self, tmp_path):
        """Test basic directory tree generation."""
        # Create a dummy directory structure
        (tmp_path / "file1.txt").touch()
        (tmp_path / "dir1").mkdir()
        (tmp_path / "dir1" / "file2.txt").touch()
        (tmp_path / "dir2").mkdir()
        (tmp_path / "dir2" / "subdir1").mkdir()
        (tmp_path / "dir2" / "subdir1" / "file3.txt").touch()

        expected_tree_output = (
            f"{tmp_path.name}/\n"
            f"├── dir1/\n"
            f"│   └── file2.txt\n"
            f"├── dir2/\n"
            f"│   └── subdir1/\n"
            f"│       └── file3.txt\n"
            f"└── file1.txt\n"
        )

        actual_tree = get_project_tree(tmp_path)
        expected_tree_output = (
            f"{tmp_path.name}/\n"
            f"├── dir1/\n"
            f"│   └── file2.txt\n"
            f"├── dir2/\n"
            f"│   └── subdir1/\n"
            f"│       └── file3.txt\n"
            f"└── file1.txt\n"
        )
        assert actual_tree.strip() == expected_tree_output.strip()

    def test_ignore_patterns(self, tmp_path):
        """Test ignoring files and directories."""
        (tmp_path / "file1.txt").touch()
        (tmp_path / "ignored_file.txt").touch()
        (tmp_path / "dir1").mkdir()
        (tmp_path / "dir1" / "file2.txt").touch()
        (tmp_path / "dir1" / "ignored_dir").mkdir()
        (tmp_path / "dir1" / "ignored_dir" / "file_in_ignored_dir.txt").touch()
        (tmp_path / ".git").mkdir()  # Often ignored

        ignore_patterns = [
            "*.txt",
            "ignored_dir",
            ".git",
        ]  # Ignore all .txt files, ignored_dir and .git

        actual_tree = get_project_tree(tmp_path, ignore_patterns=ignore_patterns)

        # Expected output: only 'dir1' should be visible at the top level, and it will be empty because its contents are ignored.
        expected_tree_output = f"{tmp_path.name}/\n├── dir1/\n"
        assert actual_tree.strip() == expected_tree_output.strip()

        actual_tree = get_project_tree(tmp_path, ignore_patterns=ignore_patterns)
        assert actual_tree.strip() == expected_tree_output.strip()

    def test_max_depth(self, tmp_path):
        """Test max_depth parameter."""
        (tmp_path / "file1.txt").touch()
        (tmp_path / "dir1").mkdir()
        (tmp_path / "dir1" / "file2.txt").touch()
        (tmp_path / "dir1" / "subdir1").mkdir()
        (tmp_path / "dir1" / "subdir1" / "file3.txt").touch()

        # max_depth = 0: only root
        expected_tree_depth_0 = f"{tmp_path.name}/\n"
        actual_tree_depth_0 = get_project_tree(tmp_path, max_depth=0)
        assert actual_tree_depth_0.strip() == expected_tree_depth_0.strip()

        # max_depth = 1: root and direct children
        expected_tree_depth_1 = f"{tmp_path.name}/\n├── dir1/\n└── file1.txt\n"
        actual_tree_depth_1 = get_project_tree(tmp_path, max_depth=1)
        assert actual_tree_depth_1.strip() == expected_tree_depth_1.strip()

        # max_depth = 2: root, direct children, and their direct children
        expected_tree_depth_2 = (
            f"{tmp_path.name}/\n├── dir1/\n│   ├── subdir1/\n│   └── file2.txt\n└── file1.txt\n"
        )
        actual_tree_depth_2 = get_project_tree(tmp_path, max_depth=2)
        assert actual_tree_depth_2.strip() == expected_tree_depth_2.strip()
