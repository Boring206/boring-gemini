"""
Code Indexer for Vector RAG

Splits Python files into semantic chunks:
- Function-level chunks
- Class-level chunks  
- Import block chunks
- Module docstrings

Uses AST parsing to extract structured information.
"""

import ast
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Iterator, Optional, Set, Dict
import logging

logger = logging.getLogger(__name__)


@dataclass
class CodeChunk:
    """A semantic chunk of code for embedding."""
    chunk_id: str
    file_path: str
    chunk_type: str  # "function", "class", "imports", "module_doc"
    name: str
    content: str
    start_line: int
    end_line: int
    dependencies: List[str] = field(default_factory=list)  # Functions/classes this chunk calls
    parent: Optional[str] = None  # Parent class if method
    signature: Optional[str] = None  # Function/class signature for quick reference
    docstring: Optional[str] = None


@dataclass 
class IndexStats:
    """Statistics about the indexed codebase."""
    total_files: int = 0
    total_chunks: int = 0
    functions: int = 0
    classes: int = 0
    methods: int = 0
    skipped_files: int = 0


class CodeIndexer:
    """
    Parse Python files and extract semantic chunks.
    
    Features:
    - AST-based parsing for accurate structure extraction
    - Dependency tracking (what each function calls)
    - Configurable chunk size limits
    """
    
    IGNORED_DIRS: Set[str] = {
        ".git", "__pycache__", "node_modules", ".venv", "venv", 
        "htmlcov", ".pytest_cache", ".mypy_cache", ".ruff_cache",
        "dist", "build", "*.egg-info", ".boring_memory"
    }
    
    IGNORED_FILES: Set[str] = {
        "__init__.py",  # Usually empty or just imports
    }
    
    def __init__(
        self, 
        project_root: Path, 
        max_chunk_tokens: int = 500,
        include_init_files: bool = False
    ):
        self.project_root = Path(project_root)
        self.max_chunk_tokens = max_chunk_tokens
        self.include_init_files = include_init_files
        self.stats = IndexStats()
    
    def index_project(self) -> Iterator[CodeChunk]:
        """
        Index all Python files in the project.
        
        Yields:
            CodeChunk objects for each semantic unit
        """
        self.stats = IndexStats()
        
        for py_file in self.project_root.rglob("*.py"):
            # Skip ignored directories
            if self._should_skip_path(py_file):
                self.stats.skipped_files += 1
                continue
            
            # Skip __init__.py unless configured otherwise
            if not self.include_init_files and py_file.name == "__init__.py":
                continue
            
            self.stats.total_files += 1
            
            try:
                for chunk in self.index_file(py_file):
                    self.stats.total_chunks += 1
                    yield chunk
            except Exception as e:
                logger.warning(f"Failed to index {py_file}: {e}")
                self.stats.skipped_files += 1
    
    def index_file(self, file_path: Path) -> Iterator[CodeChunk]:
        """
        Extract chunks from a single Python file.
        
        Args:
            file_path: Path to the Python file
            
        Yields:
            CodeChunk objects
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except SyntaxError as e:
            logger.debug(f"Syntax error in {file_path}: {e}")
            return
        except UnicodeDecodeError as e:
            logger.debug(f"Encoding error in {file_path}: {e}")
            return
        
        try:
            rel_path = str(file_path.relative_to(self.project_root))
        except ValueError:
            rel_path = str(file_path)
        
        lines = content.splitlines()
        
        # 1. Module docstring
        module_doc = ast.get_docstring(tree)
        if module_doc:
            yield CodeChunk(
                chunk_id=self._make_id(rel_path, "module_doc"),
                file_path=rel_path,
                chunk_type="module_doc",
                name=file_path.stem,
                content=module_doc,
                start_line=1,
                end_line=self._get_docstring_end_line(tree),
                docstring=module_doc
            )
        
        # 2. Top-level imports (as a single chunk)
        imports = self._extract_imports(tree, lines)
        if imports:
            yield CodeChunk(
                chunk_id=self._make_id(rel_path, "imports"),
                file_path=rel_path,
                chunk_type="imports",
                name="imports",
                content=imports["content"],
                start_line=imports["start"],
                end_line=imports["end"],
                dependencies=imports["modules"]
            )
        
        # 3. Top-level functions and classes
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                self.stats.functions += 1
                yield self._chunk_from_function(node, rel_path, lines)
                
            elif isinstance(node, ast.ClassDef):
                self.stats.classes += 1
                # Yield class header
                yield self._chunk_from_class(node, rel_path, lines)
                
                # Yield methods separately
                for method in node.body:
                    if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self.stats.methods += 1
                        yield self._chunk_from_function(
                            method, rel_path, lines, parent=node.name
                        )
    
    def _chunk_from_function(
        self, 
        node: ast.FunctionDef, 
        file_path: str, 
        lines: List[str],
        parent: Optional[str] = None
    ) -> CodeChunk:
        """Create chunk from function definition."""
        start = node.lineno - 1
        end = node.end_lineno or (start + 1)
        content = "\n".join(lines[start:end])
        
        # Extract function signature
        sig_end = start
        for i, line in enumerate(lines[start:end]):
            if ":" in line and not line.strip().startswith("#"):
                sig_end = start + i
                break
        signature = "\n".join(lines[start:sig_end + 1])
        
        # Extract docstring
        docstring = ast.get_docstring(node)
        
        # Extract function calls (dependencies)
        deps = self._extract_dependencies(node)
        
        # Build qualified name
        name = f"{parent}.{node.name}" if parent else node.name
        
        return CodeChunk(
            chunk_id=self._make_id(file_path, name),
            file_path=file_path,
            chunk_type="method" if parent else "function",
            name=node.name,
            content=content,
            start_line=node.lineno,
            end_line=end,
            dependencies=deps,
            parent=parent,
            signature=signature.strip(),
            docstring=docstring
        )
    
    def _chunk_from_class(self, node: ast.ClassDef, file_path: str, lines: List[str]) -> CodeChunk:
        """
        Create chunk from class definition (header + docstring only).
        Methods are extracted separately.
        """
        start = node.lineno - 1
        
        # Find where the class header ends (before first method)
        class_header_end = start + 1
        for child in node.body:
            if isinstance(child, ast.Expr) and isinstance(child.value, ast.Constant):
                # Docstring
                class_header_end = child.end_lineno or class_header_end
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # First method - stop before it
                break
            elif isinstance(child, ast.Assign):
                # Class variable
                class_header_end = child.end_lineno or class_header_end
        
        content = "\n".join(lines[start:class_header_end])
        
        # Extract base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(base.attr)
        
        return CodeChunk(
            chunk_id=self._make_id(file_path, node.name),
            file_path=file_path,
            chunk_type="class",
            name=node.name,
            content=content,
            start_line=node.lineno,
            end_line=class_header_end,
            dependencies=bases,  # Base classes as dependencies
            docstring=ast.get_docstring(node)
        )
    
    def _extract_dependencies(self, node: ast.AST) -> List[str]:
        """Extract all function/method calls within a node."""
        deps: Set[str] = set()
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                # Direct function call: func()
                if isinstance(child.func, ast.Name):
                    deps.add(child.func.id)
                # Method call: obj.method()
                elif isinstance(child.func, ast.Attribute):
                    deps.add(child.func.attr)
        
        # Filter out builtins and common functions
        builtins = {"print", "len", "str", "int", "float", "list", "dict", "set", 
                    "tuple", "range", "enumerate", "zip", "map", "filter", "open",
                    "isinstance", "issubclass", "hasattr", "getattr", "setattr"}
        
        return sorted(deps - builtins)
    
    def _extract_imports(self, tree: ast.Module, lines: List[str]) -> Optional[Dict]:
        """Extract import statements from module."""
        import_nodes = []
        modules = []
        
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                import_nodes.append(node)
                for alias in node.names:
                    modules.append(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                import_nodes.append(node)
                if node.module:
                    modules.append(node.module.split(".")[0])
        
        if not import_nodes:
            return None
        
        start = min(n.lineno for n in import_nodes)
        end = max(n.end_lineno or n.lineno for n in import_nodes)
        
        return {
            "content": "\n".join(lines[start - 1:end]),
            "start": start,
            "end": end,
            "modules": sorted(set(modules))
        }
    
    def _get_docstring_end_line(self, tree: ast.Module) -> int:
        """Get the ending line of module docstring."""
        if tree.body and isinstance(tree.body[0], ast.Expr):
            if isinstance(tree.body[0].value, ast.Constant):
                return tree.body[0].end_lineno or 1
        return 1
    
    def _should_skip_path(self, path: Path) -> bool:
        """Check if path should be skipped."""
        parts = path.parts
        for ignored in self.IGNORED_DIRS:
            if ignored.startswith("*"):
                # Glob pattern like *.egg-info
                if any(p.endswith(ignored[1:]) for p in parts):
                    return True
            elif ignored in parts:
                return True
        return False
    
    def _make_id(self, file_path: str, name: str) -> str:
        """Generate unique chunk ID."""
        raw = f"{file_path}::{name}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]
    
    def get_stats(self) -> IndexStats:
        """Return indexing statistics."""
        return self.stats
