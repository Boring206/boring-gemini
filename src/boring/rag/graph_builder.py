"""
Code Dependency Graph Builder

Creates call graph between functions/classes for Graph RAG.
Enables "impact zone" analysis - when modifying function A,
automatically include all callers/callees in context.
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

from .code_indexer import CodeChunk


@dataclass
class GraphStats:
    """Statistics about the dependency graph."""

    total_nodes: int = 0
    total_edges: int = 0
    avg_connections: float = 0.0
    max_callers: int = 0
    max_callees: int = 0


class DependencyGraph:
    """
    Bidirectional dependency graph for code chunks.

    Edges:
    - callers[A] = {B, C} means B and C call A
    - callees[A] = {X, Y} means A calls X and Y

    Usage:
        graph = DependencyGraph(chunks)
        callers = graph.get_callers(chunk_id)  # Who calls this?
        impact = graph.get_impact_zone(chunk_id)  # What might break?
    """

    def __init__(self, chunks: Optional[list[CodeChunk]] = None):
        self._chunks: dict[str, CodeChunk] = {}
        self._name_to_ids: dict[str, set[str]] = defaultdict(set)  # name -> chunk_ids

        # Adjacency lists
        self.callers: dict[str, set[str]] = defaultdict(set)  # who calls this
        self.callees: dict[str, set[str]] = defaultdict(set)  # this calls who

        if chunks:
            self._build(chunks)

    def _build(self, chunks: list[CodeChunk]) -> None:
        """Build the graph from chunks."""
        # First pass: register all chunks by name
        for chunk in chunks:
            self._chunks[chunk.chunk_id] = chunk

            # Register by simple name
            self._name_to_ids[chunk.name].add(chunk.chunk_id)

            # Also register by qualified name (ClassName.method)
            if chunk.parent:
                qualified = f"{chunk.parent}.{chunk.name}"
                self._name_to_ids[qualified].add(chunk.chunk_id)

        # Second pass: build edges based on dependencies
        for chunk in chunks:
            for dep_name in chunk.dependencies:
                # Find all chunks matching this dependency name
                dep_ids = self._name_to_ids.get(dep_name, set())

                for dep_id in dep_ids:
                    # chunk calls dep
                    self.callees[chunk.chunk_id].add(dep_id)
                    self.callers[dep_id].add(chunk.chunk_id)

    def add_chunk(self, chunk: CodeChunk) -> None:
        """Add a single chunk to the graph."""
        self._chunks[chunk.chunk_id] = chunk
        self._name_to_ids[chunk.name].add(chunk.chunk_id)

        if chunk.parent:
            qualified = f"{chunk.parent}.{chunk.name}"
            self._name_to_ids[qualified].add(chunk.chunk_id)

        # Build edges for this chunk
        for dep_name in chunk.dependencies:
            dep_ids = self._name_to_ids.get(dep_name, set())
            for dep_id in dep_ids:
                self.callees[chunk.chunk_id].add(dep_id)
                self.callers[dep_id].add(chunk.chunk_id)

    def get_chunk(self, chunk_id: str) -> Optional[CodeChunk]:
        """Get chunk by ID."""
        return self._chunks.get(chunk_id)

    def get_chunks_by_name(self, name: str) -> list[CodeChunk]:
        """Get all chunks matching a name."""
        ids = self._name_to_ids.get(name, set())
        return [self._chunks[cid] for cid in ids if cid in self._chunks]

    def get_callers(self, chunk_id: str) -> list[CodeChunk]:
        """
        Get all chunks that call this chunk.

        Use case: "Who depends on this function?"
        """
        caller_ids = self.callers.get(chunk_id, set())
        return [self._chunks[cid] for cid in caller_ids if cid in self._chunks]

    def get_callees(self, chunk_id: str) -> list[CodeChunk]:
        """
        Get all chunks that this chunk calls.

        Use case: "What does this function depend on?"
        """
        callee_ids = self.callees.get(chunk_id, set())
        return [self._chunks[cid] for cid in callee_ids if cid in self._chunks]

    def get_related_chunks(
        self, seed_chunks: list[CodeChunk], depth: int = 1, direction: str = "both"
    ) -> list[CodeChunk]:
        """
        Get related chunks via BFS on the dependency graph.

        Args:
            seed_chunks: Starting chunks
            depth: How many hops to traverse (default 1 per user decision)
            direction: "callers", "callees", or "both"

        Returns:
            Related chunks (excluding seeds)
        """
        visited: set[str] = {c.chunk_id for c in seed_chunks}
        frontier: set[str] = {c.chunk_id for c in seed_chunks}
        related: list[CodeChunk] = []

        for _ in range(depth):
            next_frontier: set[str] = set()

            for chunk_id in frontier:
                neighbors: set[str] = set()

                if direction in ("callers", "both"):
                    neighbors.update(self.callers.get(chunk_id, set()))

                if direction in ("callees", "both"):
                    neighbors.update(self.callees.get(chunk_id, set()))

                for neighbor_id in neighbors:
                    if neighbor_id not in visited:
                        visited.add(neighbor_id)
                        next_frontier.add(neighbor_id)
                        if neighbor_id in self._chunks:
                            related.append(self._chunks[neighbor_id])

            frontier = next_frontier

            if not frontier:
                break

        return related

    def get_impact_zone(self, modified_chunk_id: str, depth: int = 1) -> list[CodeChunk]:
        """
        Get the "impact zone" - all chunks that might break if this one changes.

        This returns all CALLERS (things that depend on the modified chunk).
        If you change a function, its callers might break.

        Args:
            modified_chunk_id: The chunk being modified
            depth: How many levels of callers to include (default 1)

        Returns:
            List of chunks that might be affected
        """
        if modified_chunk_id not in self._chunks:
            return []

        seed = [self._chunks[modified_chunk_id]]
        return self.get_related_chunks(seed, depth=depth, direction="callers")

    def get_context_for_modification(self, modified_chunk_id: str) -> dict[str, list[CodeChunk]]:
        """
        Get comprehensive context for modifying a chunk.

        Returns dict with:
        - callers: Who calls this (might break)
        - callees: What this calls (need to understand interface)
        - siblings: Other methods in same class
        """
        result = {
            "callers": self.get_callers(modified_chunk_id),
            "callees": self.get_callees(modified_chunk_id),
            "siblings": [],
        }

        chunk = self._chunks.get(modified_chunk_id)
        if chunk and chunk.parent:
            # Find other methods in the same class
            for cid, c in self._chunks.items():
                if c.parent == chunk.parent and cid != modified_chunk_id:
                    result["siblings"].append(c)

        return result

    def get_stats(self) -> GraphStats:
        """Get graph statistics."""
        total_edges = sum(len(callees) for callees in self.callees.values())
        total_nodes = len(self._chunks)

        max_callers = max((len(c) for c in self.callers.values()), default=0)
        max_callees = max((len(c) for c in self.callees.values()), default=0)

        return GraphStats(
            total_nodes=total_nodes,
            total_edges=total_edges,
            avg_connections=total_edges / total_nodes if total_nodes > 0 else 0,
            max_callers=max_callers,
            max_callees=max_callees,
        )

    def find_path(self, from_id: str, to_id: str, max_depth: int = 5) -> Optional[list[str]]:
        """
        Find shortest path between two chunks (if exists).

        Useful for understanding how two distant pieces of code are connected.
        """
        if from_id not in self._chunks or to_id not in self._chunks:
            return None

        if from_id == to_id:
            return [from_id]

        # BFS
        visited = {from_id}
        queue = [(from_id, [from_id])]

        for _ in range(max_depth):
            if not queue:
                break

            next_queue = []
            for current, path in queue:
                # Check all neighbors (both callers and callees)
                neighbors = self.callers.get(current, set()) | self.callees.get(current, set())

                for neighbor in neighbors:
                    if neighbor == to_id:
                        return path + [neighbor]

                    if neighbor not in visited:
                        visited.add(neighbor)
                        next_queue.append((neighbor, path + [neighbor]))

            queue = next_queue

        return None  # No path found within max_depth

    def visualize(self, format: str = "mermaid", max_nodes: int = 50) -> str:
        """
        Generate a visualization of the dependency graph.

        Args:
            format: Output format ("mermaid" or "json")
            max_nodes: Maximum nodes to include (for readability)

        Returns:
            String representation of the graph
        """
        if format == "json":
            import json

            nodes = []
            edges = []
            for cid, chunk in list(self._chunks.items())[:max_nodes]:
                nodes.append({"id": cid, "name": chunk.name, "type": chunk.chunk_type})
                for callee in self.callees.get(cid, set()):
                    edges.append({"from": cid, "to": callee})
            return json.dumps({"nodes": nodes, "edges": edges}, indent=2)

        # Mermaid format
        lines = ["```mermaid", "flowchart TD"]

        # Add nodes (limit for readability)
        added = set()
        for cid, chunk in list(self._chunks.items())[:max_nodes]:
            safe_name = chunk.name.replace('"', "'")
            lines.append(f'    {cid[:8]}["{safe_name}"]')
            added.add(cid)

        # Add edges
        for cid in added:
            for callee in self.callees.get(cid, set()):
                if callee in added:
                    lines.append(f"    {cid[:8]} --> {callee[:8]}")

        lines.append("```")
        return "\n".join(lines)
