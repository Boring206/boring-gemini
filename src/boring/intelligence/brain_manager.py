"""
Brain Manager Module for Boring V10.23 (Refactored Phase 4.1+)

Manages the .boring_brain knowledge base with automatic learning capabilities.
Facade for Underlying Intelligence Components.
Now supports Async ProcessPool operations for Embeddings.
"""

import asyncio
import contextlib
import contextvars
import json
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

# Try to import storage cleaner for test isolation
try:
    from boring.services.storage import _clear_thread_local_connection
except ImportError:
    _clear_thread_local_connection = None

from .brain.index_manager import InvertedIndexManager
from .brain.repository import PatternRepository

# Re-export types for backward compatibility
from .brain.types import LearnedPattern, Rubric  # noqa: F401
from .brain.vector_engine import VectorSearchEngine

# Shared Singleflight state
_GLOBAL_INFLIGHT: dict[str, asyncio.Future] = {}

# Performance: Module-level pattern cache
_pattern_cache_var: contextvars.ContextVar[dict[str, tuple[list[dict], float]] | None] = (
    contextvars.ContextVar("pattern_cache", default=None)
)


class BrainManager:
    """
    Manages .boring_brain knowledge base.
    Facade for underlying intelligence components.
    """

    def __init__(self, project_root: Path, log_dir: Path | None = None):
        self.project_root = Path(project_root)
        from boring.paths import BoringPaths

        self.paths = BoringPaths(self.project_root)

        self.brain_dir = self.paths.brain
        self.log_dir = log_dir or self.project_root / "logs"

        # Ensure DB connection is clean for new instances (fixes test isolation)
        if _clear_thread_local_connection:
            try:
                _clear_thread_local_connection()
            except Exception:
                pass

        # Initialize Components
        self.repository = PatternRepository(self.project_root, self.log_dir)
        self.vector_engine = VectorSearchEngine(self.brain_dir, self.log_dir)
        self.index_manager = InvertedIndexManager(self.brain_dir, self.log_dir)

        # Legacy Compatibility / Direct Access
        self.patterns_dir = self.brain_dir / "learned_patterns"
        self.rubrics_dir = self.brain_dir / "rubrics"
        self.adaptations_dir = self.brain_dir / "workflow_adaptations"

        self.storage = self.repository.storage
        self.index = self.index_manager.index

        # Locking
        from ..utils.lock import RobustLock

        self.brain_lock = RobustLock(self.brain_dir / "brain_lock")

        # Singleflight state
        self._inflight = _GLOBAL_INFLIGHT

        # Audit
        try:
            from ..services.audit import AuditLogger

            self.audit = AuditLogger(self.project_root)
        except ImportError:
            self.audit = None

        self._ensure_structure()
        self.index_manager.load_from_disk()
        if not self.index_manager.index.documents:
            self.index_manager.rebuild(self.repository)

        # FAISS/Vector properties delegated to vector_engine
        self.vector_engine._ensure_vector_store()

    @contextlib.contextmanager
    def brain_transaction(self):
        """Atomic transaction for Brain updates."""
        if self.brain_lock.acquire(timeout=60.0):
            try:
                self.sync()
                yield
            finally:
                self.brain_lock.release()
        else:
            raise TimeoutError("Could not acquire brain lock for transaction")

    def sync(self):
        """Fast-forward in-memory knowledge."""
        _pattern_cache_var.set(None)

    def _ensure_structure(self):
        self.log_dir.mkdir(parents=True, exist_ok=True)
        for d in [
            self.brain_dir / "workflow_adaptations",
            self.brain_dir / "learned_patterns",
            self.brain_dir / "rubrics",
        ]:
            d.mkdir(parents=True, exist_ok=True)

    def get_brain_summary(self) -> dict[str, Any]:
        """Legacy summary format."""
        patterns = self.repository.get_all(limit=1000)
        rubrics = [p.stem for p in self.rubrics_dir.glob("*.json")]
        adaptations = [p.stem for p in self.adaptations_dir.glob("*.json")]
        return {
            "patterns_count": len(patterns),
            "total_patterns": len(patterns),
            "rubrics": rubrics,
            "adaptations": adaptations,
        }

    def learn_from_memory(self, storage: Any) -> dict[str, Any]:
        """Legacy memory integration."""
        try:
            try:
                storage.get_recent_loops(limit=50)
            except AttributeError:
                pass

            try:
                errors = storage.get_top_errors(limit=10)
            except AttributeError:
                errors = []

            new_count = 0
            for err in errors:
                err_dict = (
                    err
                    if isinstance(err, dict)
                    else (getattr(err, "__dict__", {}) if hasattr(err, "__dict__") else {})
                )

                # Deterministic ID for idempotency
                problem_sig = err_dict.get("error_type", "Error")
                pattern_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, problem_sig))

                exists = self.repository.get(pattern_id)

                self.upsert_pattern(
                    context="Memory Context",
                    problem=problem_sig,
                    solution=err_dict.get("solution", "N/A"),
                    pattern_id=pattern_id,
                )

                if not exists:
                    new_count += 1

            total_patterns = len(self.repository.get_all(limit=5000))
            return {
                "status": "SUCCESS",
                "new_patterns": new_count,
                "total_patterns": total_patterns,
            }
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    def _prepare_pattern_object(self, **kwargs) -> Any:
        """Create a Pattern dataclass instance from dict args."""
        return LearnedPattern(
            pattern_id=kwargs.get("pattern_id") or str(uuid.uuid4()),
            pattern_type=kwargs.get("pattern_type", "general"),
            description=kwargs.get("problem", "N/A"),
            context=kwargs.get("context", "N/A"),
            solution=kwargs.get("solution", "N/A"),
            success_count=kwargs.get("success_count", 1),
            created_at=kwargs.get("created_at") or datetime.now().isoformat(),
            last_used=kwargs.get("last_used") or datetime.now().isoformat(),
            decay_score=kwargs.get("decay_score", 1.0),
            session_boost=kwargs.get("session_boost", 0.0),
            cluster_id=kwargs.get("cluster_id") or "",
        )

    def get_relevant_patterns(self, query: str, limit: int = 5) -> list[dict]:
        """Search patterns by query (vector or inverted fallback)."""
        if not query or not query.strip():
            patterns = self.repository.get_all(limit=limit)
            return [asdict(p) for p in patterns]

        return self._get_relevant_patterns_unsafe(query, limit)

    def _get_relevant_patterns_unsafe(self, query: str, limit: int = 5) -> list[dict]:
        """Internal search logic."""
        results = self.vector_engine.search(query, limit)
        if results:
            return results

        if self.index:
            results = self.index.search(query, limit=limit)
            return [r.get("metadata", r) if isinstance(r, dict) else r for r in results]

        return []

    # Add missing methods for tests
    def get_relevant_patterns_embedding(self, context: str, limit: int = 5) -> list[dict]:
        """Alias for tests expecting this name."""
        return self._get_relevant_patterns_unsafe(context, limit)

    @property
    def vector_store(self):
        return self.vector_engine.vector_store

    @vector_store.setter
    def vector_store(self, value):
        self.vector_engine.vector_store = value

    @property
    def faiss_index(self):
        return self.vector_engine.faiss_index

    @faiss_index.setter
    def faiss_index(self, value):
        self.vector_engine.faiss_index = value

    @property
    def faiss_patterns(self):
        return self.vector_engine.faiss_patterns

    @faiss_patterns.setter
    def faiss_patterns(self, value):
        self.vector_engine.faiss_patterns = value

    @property
    def embedding_model(self):
        return self.vector_engine.embedding_model

    @embedding_model.setter
    def embedding_model(self, value):
        self.vector_engine.embedding_model = value

    def apply_session_boost(self, *args, **kwargs):
        """Stub for GlobalKnowledgeStore compatibility."""
        pass  # No-op in facade

    def incremental_learn(
        self,
        arg1: str | None = None,
        arg2: str | None = None,
        arg3: str | None = None,
        arg4: str | None = None,
        **kwargs,
    ) -> dict:
        """
        Learn a new pattern.
        Supports two signatures for backward compatibility:
        1. (pattern_type, problem, solution, error_type=None)
        2. (context, problem, solution, error_type=None)
        """
        context = kwargs.get("context")
        problem = kwargs.get("problem")
        solution = kwargs.get("solution")
        pattern_type = kwargs.get("pattern_type", "general")
        error_type = kwargs.get("error_type")

        known_types = [
            "error_solution",
            "code_style",
            "workflow_tip",
            "performance",
            "security",
            "general",
        ]
        if arg1:
            if arg1 in known_types:
                pattern_type = arg1
                if arg2:
                    problem = arg2
                if arg3:
                    solution = arg3
                if arg4:
                    error_type = arg4
            else:
                context = arg1
                if arg2:
                    problem = arg2
                if arg3:
                    solution = arg3
                if arg4:
                    error_type = arg4

        if error_type:
            if error_type in known_types:
                pattern_type = error_type
            elif pattern_type == "general":
                pattern_type = "error_solution"

        final_context = context or error_type or "General Context"
        final_problem = problem or "Unknown Problem"
        final_solution = solution or "No solution provided"

        clean_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k not in ["context", "problem", "solution", "pattern_type", "error_type"]
        }

        res = self.upsert_pattern(
            context=final_context,
            problem=final_problem,
            solution=final_solution,
            pattern_type=pattern_type,
            **clean_kwargs,
        )
        return {"status": "SUCCESS", "pattern": asdict(res)}

    def get_pattern_stats(self) -> dict[str, Any]:
        """Return statistics about learned patterns."""
        patterns = self.repository.get_all(limit=5000)
        by_type = {}
        for p in patterns:
            pt = p.pattern_type or "general"
            by_type[pt] = by_type.get(pt, 0) + 1

        return {"total_patterns": len(patterns), "total": len(patterns), "by_type": by_type}

    def upsert_pattern(
        self, context: str, problem: str, solution: str, pattern_type: str = "general", **kwargs
    ):
        """Create or update a pattern."""
        pattern = self._prepare_pattern_object(
            context=context, problem=problem, solution=solution, pattern_type=pattern_type, **kwargs
        )
        self.repository.save(pattern)

        # Sync to components
        if self.index_manager:
            content = f"{pattern.description} {pattern.solution} {pattern.context}"
            self.index_manager.add_pattern(pattern, content)

        try:
            from dataclasses import asdict

            self._sync_patterns_to_vector([asdict(pattern)])
        except Exception:
            pass  # Vibe check: don't crash on vector sync in tests
        return pattern

    def _load_patterns(self) -> list[dict]:
        """Stub for legacy compatibility."""
        return [asdict(p) for p in self.repository.get_all()]

    def learn_pattern(self, *args, **kwargs):
        """Deprecated alias."""
        return self.incremental_learn(*args, **kwargs)

    def get_brain_health_report(self) -> dict[str, Any]:
        """Health diagnostics."""
        patterns = self.repository.get_all(limit=10)
        issues = []
        if not patterns:
            issues.append("No patterns learned yet")
        return {
            "health_status": "HEALTHY" if not issues else "STALE",
            "health_score": 100 if not issues else 50,
            "issues": issues,
            "stats": {"total_patterns": len(patterns)},
            "total_patterns": len(patterns),  # Compatibility key
        }

    def create_rubric(self, name: str, description: str, criteria: list[dict]):
        """Create a new rubric file."""
        data = {
            "name": name,
            "description": description,
            "criteria": criteria,
            "created_at": datetime.now().isoformat(),
        }
        rubric_path = self.rubrics_dir / f"{name}.json"
        rubric_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get_rubric(self, name: str) -> dict | None:
        """Load rubric by name."""
        path = self.rubrics_dir / f"{name}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return None

    def create_default_rubrics(self) -> dict[str, Any]:
        """Initialize standard rubrics."""
        self.create_rubric("implementation_plan", "Plan Quality", [])
        return {"status": "SUCCESS", "rubrics_created": ["implementation_plan"]}

    def update_pattern_decay(self):
        """Update decay scores for all patterns."""
        patterns = self.repository.get_all(limit=5000)
        updated_count = 0
        now = datetime.now()
        for p in patterns:
            try:
                last_used = datetime.fromisoformat(p.last_used)
                days_passed = (now - last_used).days
                if days_passed > 0:
                    p.decay_score *= 0.95**days_passed
                    self.repository.save(p)
                    updated_count += 1
            except (ValueError, TypeError):
                continue
        return {"updated": updated_count}

    def prune_patterns(self, min_score: float = 0.5, keep_min: int = 10):
        """Prune low-relevance patterns."""
        patterns = self.repository.get_all(limit=5000)
        if len(patterns) <= keep_min:
            return {"status": "SKIPPED", "remaining": len(patterns), "pruned_count": 0}

        pruned = 0
        for i, p in enumerate(patterns):
            if i < keep_min:
                continue
            if p.decay_score < min_score:
                self.repository.delete(p.pattern_id)
                pruned += 1
        return {"status": "SUCCESS", "remaining": len(patterns) - pruned, "pruned_count": pruned}

    def _sync_patterns_to_vector(self, patterns: list[dict]):
        """Legacy helper to sync patterns to the vector engine."""
        for p in patterns:
            try:
                pattern_obj = self._prepare_pattern_object(**p)
                self.vector_engine.add_pattern(pattern_obj)
            except Exception as e:
                import logging

                logging.getLogger(__name__).debug(f"Failed to sync pattern to vector: {e}")

    def _save_patterns(self, patterns_dict_list: list[dict]):
        """Legacy batch save support."""
        for p in patterns_dict_list:
            kwargs = p.copy()
            context = kwargs.pop("context", "N/A")
            problem = kwargs.pop("description", kwargs.pop("problem", "N/A"))
            solution = kwargs.pop("solution", "N/A")
            pattern_type = kwargs.pop("pattern_type", "general")

            self.upsert_pattern(
                context=context,
                problem=problem,
                solution=solution,
                pattern_type=pattern_type,
                metadata=p,
                **kwargs,
            )


def create_brain_manager(
    project_root: str | Path, log_dir: str | Path | None = None
) -> BrainManager:
    return BrainManager(project_root, log_dir)


class GlobalKnowledgeStore:
    """
    Manages global knowledge shared across all projects.
    Stores patterns in ~/.boring_brain/global_patterns.json
    Allows exporting from one project and importing to another.
    """

    def __init__(self):
        from boring.paths import get_boring_path

        self.global_dir = get_boring_path(Path.home(), "brain")
        self.global_patterns_file = self.global_dir / "global_patterns.json"
        self.global_dir.mkdir(parents=True, exist_ok=True)

    def update_pattern_decay(self):
        """Update decay scores for global patterns."""
        patterns = self._load_global_patterns()
        updated = 0
        now = datetime.now()
        for p in patterns:
            try:
                last_used = datetime.fromisoformat(
                    p.get("last_used", p.get("created_at", now.isoformat()))
                )
                days = (now - last_used).days
                if days > 0:
                    p["decay_score"] = p.get("decay_score", 1.0) * (0.95**days)
                    updated += 1
            except Exception:
                pass

        if updated > 0:
            self._save_global_patterns(patterns)

        return {"status": "SUCCESS", "updated": updated}

    def apply_session_boost(self, patterns: list[str]) -> int:
        """Boost relevance for specific patterns."""
        if not patterns:
            return 0

        all_patterns = self._load_global_patterns()
        boosted = 0
        for p in all_patterns:
            if any(k in p.get("context", "") or k in p.get("description", "") for k in patterns):
                p["session_boost"] = p.get("session_boost", 0.0) + 0.2
                boosted += 1

        if boosted > 0:
            self._save_global_patterns(all_patterns)
        return boosted

    def clear_session_boosts(self) -> int:
        """Reset all session boosts."""
        patterns = self._load_global_patterns()
        cleared = 0
        for p in patterns:
            if p.get("session_boost", 0) > 0:
                p["session_boost"] = 0.0
                cleared += 1
        if cleared > 0:
            self._save_global_patterns(patterns)
        return cleared

    def incremental_learn(self, context: str, problem: str, solution: str, **kwargs):
        """Add pattern to global store."""
        patterns = self._load_global_patterns()
        new_pattern = {
            "pattern_id": str(uuid.uuid4()),
            "pattern_type": "general",
            "context": context,
            "description": problem,
            "solution": solution,
            "success_count": 1,
            "created_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "decay_score": 1.0,
            "session_boost": 0.0,
            **kwargs,
        }
        patterns.append(new_pattern)
        self._save_global_patterns(patterns)
        return {"status": "SUCCESS"}

    def prune_patterns(self, min_score: float = 0.5, keep_min: int = 10):
        """Prune low-relevance global patterns."""
        patterns = self._load_global_patterns()
        if len(patterns) <= keep_min:
            return {"status": "SKIPPED", "remaining": len(patterns), "pruned_count": 0}

        pruned_count = 0
        kept_patterns = []

        for i, p in enumerate(patterns):
            if i < keep_min:
                kept_patterns.append(p)
                continue

            score = p.get("decay_score", 1.0) + p.get("session_boost", 0.0)
            if score >= min_score:
                kept_patterns.append(p)
            else:
                pruned_count += 1

        self._save_global_patterns(kept_patterns)
        return {
            "status": "SUCCESS",
            "remaining": len(kept_patterns),
            "removed": pruned_count,
            "pruned_count": pruned_count,
        }

    def get_pattern_stats(self) -> dict[str, Any]:
        """Get stats."""
        patterns = self._load_global_patterns()
        total = len(patterns)
        avg_success = sum(p.get("success_count", 0) for p in patterns) / total if total > 0 else 0
        return {"total_patterns": total, "total": total, "avg_success": avg_success}

    def sync_with_remote(self, remote_url: str | None = None) -> dict[str, Any]:
        try:
            import git

            if not (self.global_dir / ".git").exists():
                repo = git.Repo.init(self.global_dir)
            else:
                repo = git.Repo(self.global_dir)

            if remote_url:
                if "origin" in repo.remotes:
                    repo.delete_remote("origin")
                repo.create_remote("origin", remote_url)

            if "origin" not in repo.remotes:
                return {"status": "ERROR", "error": "No remote URL provided"}

            origin = repo.remotes.origin
            try:
                origin.pull(rebase=True)
            except Exception:
                pass

            repo.index.add([str(self.global_patterns_file)])
            if repo.is_dirty() or repo.untracked_files:
                repo.index.commit(f"Brain Sync: {datetime.now().isoformat()}")
                origin.push()
                return {"status": "SUCCESS", "action": "pushed_changes"}

            return {"status": "SUCCESS", "action": "up_to_date"}
        except ImportError:
            return {"status": "ERROR", "error": "gitpython not installed"}
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    def _load_global_patterns(self) -> list[dict]:
        if self.global_patterns_file.exists():
            try:
                return json.loads(self.global_patterns_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return []
        return []

    def _save_global_patterns(self, patterns: list[dict]):
        self.global_patterns_file.write_text(
            json.dumps(patterns, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def export_from_project(self, project_root: Path, min_success_count: int = 1) -> dict[str, Any]:
        brain = BrainManager(project_root)
        local_patterns = brain._load_patterns()
        quality_patterns = [
            p for p in local_patterns if p.get("success_count", 0) >= min_success_count
        ]

        if not quality_patterns:
            return {"status": "NO_PATTERNS", "exported": 0}

        global_patterns = self._load_global_patterns()
        exported_count = 0
        for pattern in quality_patterns:
            pattern["source_project"] = str(project_root.name)
            pattern["exported_at"] = datetime.now().isoformat()
            existing = [
                p for p in global_patterns if p.get("pattern_id") == pattern.get("pattern_id")
            ]
            if existing:
                if pattern.get("success_count", 0) > existing[0].get("success_count", 0):
                    existing[0].update(pattern)
                    exported_count += 1
            else:
                global_patterns.append(pattern)
                exported_count += 1
        self._save_global_patterns(global_patterns)
        return {"status": "SUCCESS", "exported": exported_count}

    def import_to_project(
        self, project_root: Path, pattern_types: list[str] | None = None
    ) -> dict[str, Any]:
        global_patterns = self._load_global_patterns()
        if not global_patterns:
            return {"status": "NO_GLOBAL_PATTERNS"}
        if pattern_types:
            global_patterns = [p for p in global_patterns if p.get("pattern_type") in pattern_types]

        brain = BrainManager(project_root)
        local_patterns = brain._load_patterns()
        local_ids = {p.get("pattern_id") for p in local_patterns}
        imported_count = 0
        for pattern in global_patterns:
            if pattern.get("pattern_id") not in local_ids:
                pattern["imported_from_global"] = True
                local_patterns.append(pattern)
                imported_count += 1

        for p in local_patterns:
            brain.upsert_pattern(**_extract_upsert_args(p))

        return {"status": "SUCCESS", "imported": imported_count}

    def list_global_patterns(self) -> list[dict]:
        patterns = self._load_global_patterns()
        return [
            {"pattern_id": p.get("pattern_id"), "description": p.get("description")}
            for p in patterns
        ]


def _extract_upsert_args(p: dict) -> dict:
    return {
        "context": p.get("context", ""),
        "problem": p.get("description", p.get("problem", "")),
        "solution": p.get("solution", ""),
        "pattern_id": p.get("pattern_id"),
        "pattern_type": p.get("pattern_type", "general"),
        "metadata": {"success_count": p.get("success_count", 0)},
    }


_global_store: GlobalKnowledgeStore | None = None


def get_global_store() -> GlobalKnowledgeStore:
    global _global_store
    if _global_store is None:
        _global_store = GlobalKnowledgeStore()
    return _global_store


def get_global_knowledge_store() -> GlobalKnowledgeStore:
    return get_global_store()
