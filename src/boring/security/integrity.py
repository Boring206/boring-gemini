"""
File Integrity Monitor for Boring V12.4

Provides checksum-based verification to detect silent file modifications.
Integrates with Shadow Mode to ensure system stability.
"""

import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FileIntegrityMonitor:
    """
    Monitors file integrity using SHA256 checksums.
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.baseline_hashes: dict[str, str] = {}
        self.monitored_paths: list[Path] = []

    def calculate_file_hash(self, file_path: Path) -> str | None:
        """Calculate SHA256 hash of a file."""
        try:
            if not file_path.exists() or not file_path.is_file():
                return None

            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                # Read in 64k chunks
                for byte_block in iter(lambda: f.read(65536), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.warning(f"Failed to hash file {file_path}: {e}")
            return None

    def snapshot_files(self, paths: list[Path]) -> dict[str, str]:
        """
        Take a snapshot of file hashes.

        Args:
            paths: List of file paths or directories to monitor.

        Returns:
            Dictionary of {relative_path: hash}
        """
        hashes = {}
        self.monitored_paths = paths

        for path in paths:
            if path.is_file():
                h = self.calculate_file_hash(path)
                if h:
                    rel_path = str(path.relative_to(self.project_root))
                    hashes[rel_path] = h
            elif path.is_dir():
                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        h = self.calculate_file_hash(file_path)
                        if h:
                            try:
                                rel_path = str(file_path.relative_to(self.project_root))
                                hashes[rel_path] = h
                            except ValueError:
                                # Path not relative to project root
                                hashes[str(file_path)] = h

        self.baseline_hashes = hashes
        return hashes

    def detect_silent_modifications(self) -> list[str]:
        """
        Detect files that have changed since the last snapshot.

        Returns:
            List of modified file paths (relative).
        """
        modified_files = []

        # Check all previously hashed files
        for rel_path, old_hash in self.baseline_hashes.items():
            full_path = self.project_root / rel_path
            current_hash = self.calculate_file_hash(full_path)

            if current_hash is None:
                # File deleted
                modified_files.append(f"{rel_path} (DELETED)")
            elif current_hash != old_hash:
                modified_files.append(rel_path)

        return modified_files

    def update_baseline(self):
        """Update monitor baseline to current state."""
        if self.monitored_paths:
            self.snapshot_files(self.monitored_paths)
