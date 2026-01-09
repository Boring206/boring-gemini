import json
import re
import shutil
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings
from ..logger import log_status


@dataclass
class WorkflowMetadata:
    """Metadata for a workflow package."""

    name: str
    version: str
    description: str
    author: str = "Anonymous"
    created_at: float = 0.0
    tags: list[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.created_at == 0.0:
            self.created_at = time.time()


@dataclass
class WorkflowPackage:
    """
    Represents a portable workflow package (.bwf.json).
    Include metadata and the actual markdown content.
    """

    metadata: WorkflowMetadata
    content: str  # The markdown content
    config: Optional[dict[str, Any]] = None  # Optional extra config

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "WorkflowPackage":
        """Deserialize from JSON string with validation."""
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        if not isinstance(data, dict):
            raise ValueError("Workflow package must be a JSON object")

        # Validate required fields
        required = ["metadata", "content"]
        missing = [f for f in required if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        meta_data = data.get("metadata", {})
        if not isinstance(meta_data, dict):
            raise ValueError("Metadata must be an object")

        # Filter valid fields for Metadata to avoid crashes on extra keys
        valid_keys = {"name", "version", "description", "author", "created_at", "tags"}
        filtered_meta = {k: v for k, v in meta_data.items() if k in valid_keys}

        # Ensure name exists (required by dataclass)
        if "name" not in filtered_meta:
            raise ValueError("Metadata missing 'name'")

        # Provide defaults for others if missing in filtered (dataclass has defaults for some)
        if "version" not in filtered_meta:
            filtered_meta["version"] = "0.0.0"
        if "description" not in filtered_meta:
            filtered_meta["description"] = "No description"

        metadata = WorkflowMetadata(**filtered_meta)
        return cls(metadata=metadata, content=data.get("content", ""), config=data.get("config"))


class WorkflowManager:
    """
    Manages the lifecycle of Boring Workflows:
    - Discovery (Local)
    - Exporting (Packaging)
    - Installing (Importing)
    """

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or settings.PROJECT_ROOT
        self.workflows_dir = self.project_root / ".agent" / "workflows"
        self.base_dir = self.workflows_dir / "_base"

        # Ensure directories exist
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _parse_frontmatter(self, content: str) -> dict[str, str]:
        """Robustly parse YAML frontmatter from markdown."""
        metadata = {}
        # Regex to find frontmatter block
        match = re.search(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if match:
            yaml_block = match.group(1)
            # Simple line-based YAML parser (dependency-free)
            for line in yaml_block.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()
        return metadata

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_url(self, url: str) -> str:
        """Fetch URL content with retry logic."""
        log_status(self.project_root / "logs", "INFO", f"Downloading workflow from {url}...")
        with urllib.request.urlopen(url, timeout=10) as response:  # nosec B310: URL is user-supplied and supported
            return response.read().decode("utf-8")

    def list_local_workflows(self) -> list[str]:
        """List all available .md workflows in the project."""
        if not self.workflows_dir.exists():
            return []
        return [f.stem for f in self.workflows_dir.glob("*.md")]

    def export_workflow(self, name: str, author: str = "user") -> tuple[Optional[Path], str]:
        """
        Package a local workflow into a .bwf.json file.

        Args:
            name: Workflow name (without .md or .json)
            author: Author name

        Returns:
            (Path to created file, Message)
        """
        source_file = self.workflows_dir / f"{name}.md"
        if not source_file.exists():
            return None, f"Workflow '{name}' not found."

        try:
            content = source_file.read_text(encoding="utf-8")

            # Use robust parser
            fm_data = self._parse_frontmatter(content)
            description = fm_data.get("description", f"Exported workflow: {name}")
            tags = []

            # Create package
            metadata = WorkflowMetadata(
                name=name, version="1.0.0", description=description, author=author, tags=tags
            )

            package = WorkflowPackage(metadata=metadata, content=content)

            # Write to file
            output_filename = f"{name}.bwf.json"
            output_path = self.project_root / output_filename
            output_path.write_text(package.to_json(), encoding="utf-8")

            return output_path, f"Successfully exported to {output_filename}"

        except Exception as e:
            return None, f"Export failed: {str(e)}"

    def install_workflow(self, source: str) -> tuple[bool, str]:
        """
        Install a workflow from a local file path or a URL.

        Args:
            source: File path (e.g., 'my-flow.bwf.json') or URL

        Returns:
            (Success boolean, Message)
        """
        try:
            pkg_json = ""

            # 1. Fetch content
            if source.startswith(("http://", "https://")):
                pkg_json = self._fetch_url(source)
            else:
                # Local file
                path = Path(source)
                if not path.is_absolute():
                    path = self.project_root / path

                if not path.exists():
                    return False, f"Source file not found: {source}"

                pkg_json = path.read_text(encoding="utf-8")

            # 2. Parse & Validate
            try:
                package = WorkflowPackage.from_json(pkg_json)
            except json.JSONDecodeError:
                return False, "Invalid JSON format."
            except Exception as e:
                return False, f"Invalid workflow package structure: {e}"

            # 3. Install
            target_name = package.metadata.name
            target_file = self.workflows_dir / f"{target_name}.md"

            # Backup existing if present
            if target_file.exists():
                backup_path = self.base_dir / f"{target_name}.md.bak"
                shutil.copy2(target_file, backup_path)
                log_status(
                    self.project_root / "logs",
                    "INFO",
                    f"Backed up existing workflow to {backup_path.name}",
                )

            # Write new content
            target_file.write_text(package.content, encoding="utf-8")

            return (
                True,
                f"Successfully installed workflow '{target_name}' (v{package.metadata.version}) by {package.metadata.author}",
            )

        except urllib.error.URLError as e:
            return False, f"Network error: {e}"
        except Exception as e:
            return False, f"Installation failed: {str(e)}"

    def publish_workflow(self, name: str, token: str, public: bool = True) -> tuple[bool, str]:
        """
        Publish a workflow to GitHub Gist (The "Serverless Registry").

        Args:
            name: Workflow name
            token: GitHub Personal Access Token
            public: Whether to make the Gist public

        Returns:
            (Success, Message/URL)
        """
        source_file = self.workflows_dir / f"{name}.md"
        if not source_file.exists():
            return False, f"Workflow '{name}' not found."

        try:
            # 1. Export locally first to get JSON content
            export_path, _ = self.export_workflow(name, "Anonymous")
            if not export_path:
                return False, "Failed to package workflow."

            content = export_path.read_text(encoding="utf-8")
            filename = f"{name}.bwf.json"

            # 2. Upload to GitHub Gist
            log_status(self.project_root / "logs", "INFO", f"Publishing '{name}' to GitHub Gist...")

            payload = {
                "description": f"Boring Workflow: {name}",
                "public": public,
                "files": {filename: {"content": content}},
            }

            req = urllib.request.Request(
                "https://api.github.com/gists",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "Boring-Agent",
                },
                method="POST",
            )

            with urllib.request.urlopen(req) as response:  # nosec B310: URL is trusted GitHub Gist
                result = json.loads(response.read().decode("utf-8"))
                result.get("html_url")
                # Get raw url of the file
                raw_url = result["files"][filename]["raw_url"]

                # Cleanup temporary export file
                if export_path.exists():
                    export_path.unlink()

                return True, f"Scan this to install:\nboring workflow install {raw_url}"

        except urllib.error.HTTPError as e:
            if e.code == 401:
                return False, "Authentication failed. Check your GITHUB_TOKEN."
            return False, f"GitHub API Error: {e.code} {e.reason}"
        except Exception as e:
            return False, f"Publish failed: {str(e)}"
