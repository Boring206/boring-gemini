"""
Brain Exporter/Importer - Knowledge Transfer System.

Features:
- Export ChromaDB collections to .boring-brain (Zip/JSONL).
- Import knowledge from .boring-brain files.
- Merge strategies (Upsert).
"""

import json
import logging
import zipfile
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.progress import track

from boring.core.config import settings
from boring.intelligence.brain.vector_engine import VectorSearchEngine

logger = logging.getLogger(__name__)
console = Console()


class BrainExporter:
    """Manages export and import of brain knowledge."""

    def __init__(self, brain_dir: Path):
        self.brain_dir = brain_dir
        self.engine = VectorSearchEngine(brain_dir)
        # Force init client
        self.engine._ensure_vector_store()
        self.client = self.engine.vector_store_client

    def export_brain(self, output_path: Path, collections: list[str] | None = None):
        """
        Export collections to a .boring-brain file.

        Args:
            output_path: Target .boring-brain (zip) file.
            collections: List of collection names to export (None for all).
        """
        if not self.client:
            console.print("[red]Vector Store not initialized.[/red]")
            return

        all_cols = self.client.list_collections()
        target_cols = collections or [c.name for c in all_cols]

        console.print(f"[blue]Exporting {len(target_cols)} collections...[/blue]")

        # Create a temporary directory structure in memory (using ZipFile)
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. Manifest
            manifest = {
                "created_at": datetime.now().isoformat(),
                "boring_version": "15.0.0",
                "collections": target_cols,
                "exported_by": settings.USER_NAME or "anonymous",
            }
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))

            # 2. Iterate Collections
            for col_name in track(target_cols, description="Dumping collections..."):
                try:
                    col = self.client.get_collection(col_name)
                    # Fetch ALL data
                    data = col.get(include=["documents", "metadatas", "embeddings"])

                    ids = data["ids"]
                    documents = data.get("documents", [])
                    metadatas = data.get("metadatas", [])
                    embeddings = data.get("embeddings", [])

                    # Write JSONL
                    jsonl_lines = []
                    for i, doc_id in enumerate(ids):
                        record = {
                            "id": doc_id,
                            "document": documents[i] if documents else None,
                            "metadata": metadatas[i] if metadatas else {},
                            "embedding": embeddings[i] if embeddings else None,
                        }
                        jsonl_lines.append(json.dumps(record))

                    zf.writestr(f"collections/{col_name}.jsonl", "\n".join(jsonl_lines))

                except Exception as e:
                    logger.error(f"Failed to export collection {col_name}: {e}")
                    console.print(f"[yellow]Skipped {col_name}: {e}[/yellow]")

        console.print(f"[green]Brain exported to {output_path}[/green]")

    def import_brain(self, source_path: Path, merge: bool = True):
        """
        Import knowledge from a .boring-brain file.
        """
        if not source_path.exists():
            console.print(f"[red]Source file not found: {source_path}[/red]")
            return

        with zipfile.ZipFile(source_path, "r") as zf:
            # 1. Check Manifest
            try:
                manifest = json.loads(zf.read("manifest.json"))
                console.print(f"[blue]Importing Brain from {manifest.get('created_at')}[/blue]")
            except Exception:
                console.print("[red]Invalid .boring-brain file (missing manifest).[/red]")
                return

            # 2. Import Collections
            file_list = zf.namelist()
            collection_files = [
                f for f in file_list if f.startswith("collections/") and f.endswith(".jsonl")
            ]

            for col_file in track(collection_files, description="Merging knowledge..."):
                col_name = Path(col_file).stem

                try:
                    # Get or Create Collection
                    # Note: We use the engine's default embedding function to ensure compatibility
                    # If imported embeddings are present, use them directly (bypass calc)
                    col = self.client.get_or_create_collection(
                        name=col_name, embedding_function=self.engine.embedding_function
                    )

                    # Read Data
                    content = zf.read(col_file).decode("utf-8")
                    lines = content.strip().split("\n")

                    ids_batch = []
                    docs_batch = []
                    metas_batch = []
                    embeds_batch = []

                    for line in lines:
                        if not line.strip():
                            continue
                        record = json.loads(line)

                        ids_batch.append(record["id"])
                        docs_batch.append(record["document"])
                        metas_batch.append(record["metadata"])
                        embeds_batch.append(record["embedding"])

                    if not ids_batch:
                        continue

                    # Upsert
                    col.upsert(
                        ids=ids_batch,
                        documents=docs_batch,
                        metadatas=metas_batch,
                        embeddings=embeds_batch,
                    )

                except Exception as e:
                    logger.error(f"Failed to import {col_name}: {e}")
                    console.print(f"[yellow]Error importing {col_name}: {e}[/yellow]")

        console.print("[green]Brain import completed successfully.[/green]")
