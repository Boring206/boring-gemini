"""
Graph RAG 2.0 Service (NetworkX Backend).
Provides structural code understanding via Dependency Graph.
"""

import logging
from dataclasses import dataclass
from typing import Any

from .code_indexer import CodeChunk

logger = logging.getLogger(__name__)

try:
    import networkx as nx

    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    logger.warning("NetworkX not found. Graph RAG specific features will be limited.")


@dataclass
class GraphNode:
    chunk_id: str
    name: str
    type: str
    file_path: str


@dataclass
class GraphStats:
    """Statistics about the dependency graph."""

    total_nodes: int = 0
    total_edges: int = 0
    avg_connections: float = 0.0
    max_callers: int = 0
    max_callees: int = 0


class GraphRAG:
    """
    Advanced RAG using Graph Analysis (NetworkX).
    Traverses code dependencies (Callers/Callees/Imports).
    """

    def __init__(self, chunks: list[CodeChunk] | None = None):
        self.graph = nx.DiGraph() if HAS_NETWORKX else None
        self._node_map: dict[str, CodeChunk] = {}
        self._name_index: dict[str, set[str]] = {}

        if chunks:
            self.build(chunks)

    def build(self, chunks: list[CodeChunk]):
        """Build dependency graph from code chunks."""
        if not HAS_NETWORKX:
            return

        self.graph.clear()
        self._node_map.clear()
        self._name_index.clear()

        # Pass 1: Add Nodes and Index
        for chunk in chunks:
            self._node_map[chunk.chunk_id] = chunk
            self.graph.add_node(
                chunk.chunk_id, name=chunk.name, type=chunk.chunk_type, file=chunk.file_path
            )

            # Update Name Index
            if chunk.name not in self._name_index:
                self._name_index[chunk.name] = set()
            self._name_index[chunk.name].add(chunk.chunk_id)

            # Qualified Name Index (e.g. class.method)
            if chunk.parent:
                qname = f"{chunk.parent}.{chunk.name}"
                if qname not in self._name_index:
                    self._name_index[qname] = set()
                self._name_index[qname].add(chunk.chunk_id)

        # Pass 2: Add Edges (Dependencies)
        for chunk in chunks:
            for dep_name in chunk.dependencies:
                targets = self._resolve_dependency(dep_name, chunk)
                for target_id in targets:
                    if target_id != chunk.chunk_id:
                        self.graph.add_edge(chunk.chunk_id, target_id, type="calls")

    def add_chunk(self, chunk: CodeChunk) -> None:
        """Add a single chunk (Incremental Update)."""
        if not HAS_NETWORKX or not self.graph:
            return

        self._node_map[chunk.chunk_id] = chunk
        self.graph.add_node(
            chunk.chunk_id, name=chunk.name, type=chunk.chunk_type, file=chunk.file_path
        )

        # Update Indices (Simplified for brevity, usually should refactor _index logic)
        if chunk.name not in self._name_index:
            self._name_index[chunk.name] = set()
        self._name_index[chunk.name].add(chunk.chunk_id)

        if chunk.parent:
            qname = f"{chunk.parent}.{chunk.name}"
            if qname not in self._name_index:
                self._name_index[qname] = set()
            self._name_index[qname].add(chunk.chunk_id)

        # Edges
        for dep_name in chunk.dependencies:
            targets = self._resolve_dependency(dep_name, chunk)
            for target_id in targets:
                if target_id != chunk.chunk_id:
                    self.graph.add_edge(chunk.chunk_id, target_id, type="calls")

    def _resolve_dependency(self, dep_name: str, source_chunk: CodeChunk) -> set[str]:
        """
        Resolve a dependency name to chunk IDs.
        Implements heuristics for qualified names and local imports.
        """
        targets = set()

        # 1. Exact Name Match
        if dep_name in self._name_index:
            targets.update(self._name_index[dep_name])

        # 2. Heuristic: If source is in Class A, dep might be A.dep
        if source_chunk.parent:
            sibling_name = f"{source_chunk.parent}.{dep_name}"
            if sibling_name in self._name_index:
                targets.update(self._name_index[sibling_name])

        # 3. Heuristic: Check if dep is a class in the same file
        # (Simplified: exact match typically covers this if unique names)

        return targets

    def query(self, target_name: str, radius: int = 1) -> dict[str, list[dict[str, Any]]]:
        """
        Query the graph for a token/name.
        Returns context: definition, callers, callees.
        """
        if not HAS_NETWORKX or not self.graph:
            return {"error": "Graph engine not available"}

        # Find target node(s)
        seed_ids = self._name_index.get(target_name, set())
        if not seed_ids:
            # Try fuzzy or partial?
            return {"status": "not_found", "matches": []}

        results = []
        for seed_id in seed_ids:
            chunk = self._node_map[seed_id]

            # Get ego graph (radius)
            # Find callers (predecessors) and callees (successors)
            callers = []
            for pred in self.graph.predecessors(seed_id):
                pred_chunk = self._node_map[pred]
                callers.append(
                    {
                        "name": pred_chunk.name,
                        "file": pred_chunk.file_path,
                        "preview": pred_chunk.content[:100],
                    }
                )

            callees = []
            for succ in self.graph.successors(seed_id):
                succ_chunk = self._node_map[succ]
                callees.append({"name": succ_chunk.name, "file": succ_chunk.file_path})

            results.append(
                {
                    "definition": {
                        "name": chunk.name,
                        "file": chunk.file_path,
                        "content": chunk.content,
                    },
                    "callers": callers,
                    "callees": callees,
                    "stats": {
                        "in_degree": self.graph.in_degree(seed_id),
                        "out_degree": self.graph.out_degree(seed_id),
                    },
                }
            )

        return {"status": "success", "results": results}

    def get_centrality(self, top_k: int = 10) -> list[dict[str, Any]]:
        """Identify critical nodes (PageRank/Degree)."""
        if not HAS_NETWORKX or not self.graph:
            return []

        centrality = nx.degree_centrality(self.graph)
        sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:top_k]

        output = []
        for nid, score in sorted_nodes:
            c = self._node_map[nid]
            output.append({"name": c.name, "file": c.file_path, "score": score})
        return output

    def get_related_chunks(
        self, seed_chunks: list[CodeChunk], depth: int = 1, direction: str = "both"
    ) -> list[CodeChunk]:
        """Get related chunks via BFS (Compatibility Method)."""
        if not HAS_NETWORKX or not self.graph:
            return []

        seed_ids = {c.chunk_id for c in seed_chunks if c.chunk_id in self._node_map}
        visited = set(seed_ids)
        frontier = set(seed_ids)
        related = []

        for _ in range(depth):
            next_frontier = set()
            for nid in frontier:
                neighbors = set()
                if direction in ("callers", "both"):
                    neighbors.update(self.graph.predecessors(nid))
                if direction in ("callees", "both"):
                    neighbors.update(self.graph.successors(nid))

                for n in neighbors:
                    if n not in visited:
                        visited.add(n)
                        next_frontier.add(n)
                        related.append(self._node_map[n])
            frontier = next_frontier
            if not frontier:
                break

        return related

    def get_impact_zone(self, modified_chunk_id: str, depth: int = 1) -> list[CodeChunk]:
        """Get callers recursively (Reverse Dependency)."""
        if modified_chunk_id not in self._node_map:
            return []
        seed = [self._node_map[modified_chunk_id]]
        return self.get_related_chunks(seed, depth=depth, direction="callers")

    def get_callers(self, chunk_id: str) -> list[CodeChunk]:
        """Get direct callers."""
        return self.get_impact_zone(chunk_id, depth=1)

    def get_callees(self, chunk_id: str) -> list[CodeChunk]:
        """Get direct dependencies."""
        if not HAS_NETWORKX or not self.graph or chunk_id not in self._node_map:
            return []
        return [self._node_map[n] for n in self.graph.successors(chunk_id)]

    def get_stats(self) -> GraphStats:
        """Get graph statistics (Compatibility with GraphStats dataclass)."""
        if not HAS_NETWORKX or not self.graph:
            return GraphStats()

        nodes = self.graph.number_of_nodes()
        edges = self.graph.number_of_edges()
        if nodes > 0:
            in_degrees = [d for n, d in self.graph.in_degree()]
            out_degrees = [d for n, d in self.graph.out_degree()]
            max_in = max(in_degrees) if in_degrees else 0
            max_out = max(out_degrees) if out_degrees else 0
        else:
            max_in = 0
            max_out = 0

        return GraphStats(
            total_nodes=nodes,
            total_edges=edges,
            avg_connections=edges / nodes if nodes else 0,
            max_callers=max_in,
            max_callees=max_out,
        )

    def get_chunk(self, chunk_id: str) -> CodeChunk | None:
        """Get chunk by ID."""
        return self._node_map.get(chunk_id)

    def get_chunks_by_name(self, name: str) -> list[CodeChunk]:
        """Get chunks matching a name (exact match on short name or fully qualified)."""
        ids = self._name_index.get(name, set())
        # Also try partial matches if needed? DependencyGraph did?
        # DependencyGraph just used _name_map[name] -> set of IDs.
        return [self._node_map[cid] for cid in ids if cid in self._node_map]

    def get_context_for_modification(self, chunk_id: str) -> dict[str, list[CodeChunk]]:
        """Get structured context for modification."""
        result = {"callers": [], "callees": [], "siblings": []}
        if chunk_id not in self._node_map:
            return result

        chunk = self._node_map[chunk_id]

        # Callers
        result["callers"] = self.get_impact_zone(chunk_id)

        # Callees
        result["callees"] = self.get_callees(chunk_id)

        # Siblings (Same parent)
        if chunk.parent:
            self._name_index.get(chunk.parent, set())
            # Or assume parent is a chunk? If parent is a class name.
            # We iterate all chunks to find those with same parent. Slow.
            # Index optimization: self._parent_index?
            # For now, just scan name index if parent is in it?
            # Or skip siblings optimization for now, GraphRAG usually uses graph.
            # If graph has "contains" edges, usage would be better.
            pass

        return result

    def visualize(self, format: str = "mermaid", max_nodes: int = 50) -> str:
        """Visualize graph."""
        if not HAS_NETWORKX or not self.graph:
            return "Graph not available."

        if format == "json":
            # Return JSON structure
            data = nx.node_link_data(self.graph)
            # Filter for size?
            import json

            return json.dumps(data, indent=2)

        # Mermaid
        lines = ["```mermaid", "flowchart TD"]

        # Select top nodes by centrality or just first N
        nodes = list(self.graph.nodes())[:max_nodes]
        node_set = set(nodes)

        for nid in nodes:
            chunk = self._node_map[nid]
            safe_name = chunk.name.replace('"', "'")
            lines.append(f'    {nid[:8]}["{safe_name}"]')

        for u, v in self.graph.edges():
            if u in node_set and v in node_set:
                lines.append(f"    {u[:8]} --> {v[:8]}")

        lines.append("```")
        return "\n".join(lines)
