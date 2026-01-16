import json
import logging
import shutil
from pathlib import Path

from rich.console import Console

from boring.core.config import settings

console = Console()
logger = logging.getLogger(__name__)


class TeamSyncManager:
    """
    Manages Enterprise synchronization for Team Brain and Team RAG.
    Supports Git-based sharing for light data and remote storage for large indices.
    """

    def __init__(self, project_root: Path | None = None):
        self.root = project_root or Path(settings.PROJECT_ROOT)
        self.brain_dir = self.root / ".boring" / "brain"
        self.rag_dir = self.root / ".boring" / "rag"

        # Team Config
        self.team_config_path = self.root / ".boring" / "team_config.json"
        self.team_config = self._load_config()

    def _load_config(self) -> dict:
        if self.team_config_path.exists():
            try:
                return json.loads(self.team_config_path.read_text("utf-8"))
            except Exception as e:
                logger.error(f"Failed to load team config: {e}")
        return {}

    def sync_brain(self, direction: str = "pull"):
        """
        Phase 4.5: Team Brain Sharing (Git-based).
        Synchronize learned patterns and skills with the team repository.
        """
        console.print(f"[bold blue]🔄 Syncing Team Brain ({direction})...[/bold blue]")

        # Check if brain sharing is enabled
        sharing_url = self.team_config.get("brain_repo")
        if not sharing_url:
            console.print("[yellow]⚠️ Team Brain sharing URL missing in team_config.json[/yellow]")
            return False

        try:
            from git import Repo

            # Logic: Brain is usually stored in ~/.boring/brain or project .boring/brain
            # For Team Sharing, we might maintain a separate git repo in .boring/team_brain
            team_brain_dir = self.root / ".boring" / "team_brain"

            if not team_brain_dir.exists():
                console.print(f"[dim]Cloning team brain from {sharing_url}...[/dim]")
                Repo.clone_from(sharing_url, team_brain_dir)

            repo = Repo(team_brain_dir)

            if direction == "pull":
                repo.remotes.origin.pull()
                # Merging newly pulled patterns into active brain
                self._merge_brain_dirs(team_brain_dir, self.brain_dir)
                console.print("[green]✅ Team Brain updated![/green]")
            else:
                # Push active brain patterns to team repo
                self._merge_brain_dirs(self.brain_dir, team_brain_dir)
                repo.git.add(all=True)
                if repo.is_dirty():
                    repo.index.commit("Boring sync: update team patterns")
                    repo.remotes.origin.push()
                    console.print("[green]✅ Local patterns pushed to Team Brain![/green]")
                else:
                    console.print("[dim]Brain is already in sync.[/dim]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Brain sync failed: {e}[/red]")
            return False

    def sync_rag(self, direction: str = "pull"):
        """
        Phase 4.6: Team RAG Sync (Remote Storage).
        Synchronize RAG indices using S3, GCS, or a shared network drive.
        """
        console.print(f"[bold blue]🔄 Syncing Team RAG ({direction})...[/bold blue]")

        provider = self.team_config.get("rag_provider", "filesystem")

        if provider == "filesystem":
            shared_path = self.team_config.get("rag_shared_path")
            if not shared_path:
                console.print("[yellow]⚠️ RAG shared path missing.[/yellow]")
                return False

            shared_dir = Path(shared_path)
            if direction == "pull":
                if shared_dir.exists():
                    shutil.copytree(shared_dir, self.rag_dir, dirs_exist_ok=True)
                    console.print("[green]✅ RAG Index pulled from shared drive.[/green]")
                else:
                    console.print(f"[red]❌ Shared RAG path not found: {shared_path}[/red]")
            else:
                shutil.copytree(self.rag_dir, shared_dir, dirs_exist_ok=True)
                console.print("[green]✅ Local RAG Index pushed to shared drive.[/green]")
            return True

        # Future: S3 / GCS support
        console.print(
            f"[yellow]⚠️ Provider '{provider}' not yet fully implemented for RAG sync.[/yellow]"
        )
        return False

    def _merge_brain_dirs(self, src: Path, dst: Path):
        """Helper to merge JSON patterns between directories."""
        if not src.exists():
            return
        dst.mkdir(parents=True, exist_ok=True)

        for f in src.glob("*.json"):
            target = dst / f.name
            if not target.exists():
                shutil.copy2(f, target)
            else:
                # Basic merge logic for patterns
                with open(f, encoding="utf-8") as sf, open(target, encoding="utf-8") as df:
                    try:
                        s_data = json.load(sf)
                        d_data = json.load(df)
                        # Assume they are dicts, update destination with new keys
                        if isinstance(s_data, dict) and isinstance(d_data, dict):
                            d_data.update(s_data)
                            with open(target, "w", encoding="utf-8") as out:
                                json.dump(d_data, out, indent=2)
                    except Exception:
                        shutil.copy2(f, target)
