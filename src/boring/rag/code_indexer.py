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
import os
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
    script_chunks: int = 0
    skipped_files: int = 0


class CodeIndexer:
    """
    Parse Python files and extract semantic chunks.
    
    Features:
    - AST-based parsing for accurate structure extraction
    - Dependency tracking (what each function calls)
    - Configurable chunk size limits
    """
    
    SUPPORTED_EXTENSIONS: Set[str] = {
        ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".c", ".cpp", ".h", ".hpp", ".java", ".md"
    }
    
    IGNORED_DIRS: Set[str] = {
        ".git", "__pycache__", "node_modules", ".venv", "venv", 
        "htmlcov", ".pytest_cache", ".mypy_cache", ".ruff_cache",
        "dist", "build", "*.egg-info", ".boring_memory"
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
        Index all supported files in the project.
        
        Yields:
            CodeChunk objects for each semantic unit
        """
        self.stats = IndexStats()
        
        # Walk through all files and filter by extension
        for root, dirs, files in os.walk(self.project_root):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if not self._should_skip_dir(d)]
            
            for file in files:
                file_path = Path(root) / file
                ext = file_path.suffix.lower()
                
                if ext not in self.SUPPORTED_EXTENSIONS:
                    continue
                
                if not self.include_init_files and file == "__init__.py":
                    continue
                
                self.stats.total_files += 1
                
                try:
                    for chunk in self.index_file(file_path):
                        self.stats.total_chunks += 1
                        yield chunk
                except Exception as e:
                    logger.warning(f"Failed to index {file_path}: {e}")
                    self.stats.skipped_files += 1

    def index_file(self, file_path: Path) -> Iterator[CodeChunk]:
        """
        Extract chunks from a file (AST for Python, line-based for others).
        """
        if file_path.suffix.lower() == ".py":
            yield from self._index_python_file(file_path)
        else:
            yield from self._index_universal_file(file_path)
    
    def _should_skip_dir(self, dir_name: str) -> bool:
        """Helper to check if a directory should be skipped during walk."""
        return dir_name in self.IGNORED_DIRS or any(dir_name.endswith(ex[1:]) for ex in self.IGNORED_DIRS if ex.startswith("*"))

    def _get_rel_path(self, file_path: Path) -> str:
        """Get relative path from project root."""
        try:
            rel_path = str(file_path.relative_to(self.project_root))
            return rel_path.replace("\\", "/")
        except ValueError:
            return str(file_path).replace("\\", "/")

    def _index_universal_file(self, file_path: Path) -> Iterator[CodeChunk]:
        """
        Smart chunking for non-Python files using Tree-sitter or regex fallback.
        Supports C-style languages (JS, TS, Java, C++, Go, Rust) and Markdown.
        """
        import re
        try:
            from .parser import TreeSitterParser
            ts_parser = TreeSitterParser()
        except ImportError:
            ts_parser = None

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.debug(f"Error reading {file_path}: {e}")
            return
            
        rel_path = self._get_rel_path(file_path)
        
        # 1. Try Tree-sitter Parsing
        if ts_parser and ts_parser.is_available():
            ts_chunks = ts_parser.parse_file(file_path)
            if ts_chunks:
                for chunk in ts_chunks:
                     yield CodeChunk(
                        chunk_id=self._make_id(rel_path, f"{chunk.type}_{chunk.name}"),
                        file_path=rel_path,
                        chunk_type=f"code_{chunk.type}",
                        name=chunk.name,
                        content=chunk.content,
                        start_line=chunk.start_line,
                        end_line=chunk.end_line
                    )
                # If we got chunks, assume we handled the file well enough (for now).
                # Optionally we could index the gaps as well, but definitions are key.
                return

        # 2. Fallback to Smart Regex Chunking (if Tree-sitter unavailable or unsupported language)
        lines = content.splitlines()
        
        # Regex patterns for common block starts
        # C/C++/Java/JS/TS/Go/Rust function/class definitions
        block_start = re.compile(r'^\s*(?:export\s+)?(?:public\s+|private\s+|protected\s+)?(?:async\s+)?(?:func|function|class|interface|struct|impl|const|let|var|type|def)\s+([a-zA-Z0-9_]+)')
        # Markdown headers
        md_header = re.compile(r'^#{1,3}\s+(.+)')
        
        chunks = []
        current_chunk_lines = []
        current_start_line = 1
        current_name = file_path.name
        
        for i, line in enumerate(lines):
            line_num = i + 1
            
            # Check for new block start if current chunk is getting big enough
            # or if we are just starting
            is_start = block_start.match(line) or md_header.match(line)
            
            # Decide to yield current chunk
            # 1. New block detected AND current chunk is substantial (>5 lines)
            # 2. Current chunk is too big (>50 lines)
            if (is_start and len(current_chunk_lines) > 5) or len(current_chunk_lines) >= 50:
                 if current_chunk_lines:
                     # Yield previous chunk
                     chunk_content = "\n".join(current_chunk_lines)
                     yield CodeChunk(
                         chunk_id=self._make_id(rel_path, f"chunk_{current_start_line}"),
                         file_path=rel_path,
                         chunk_type="code_block",
                         name=current_name,
                         content=chunk_content,
                         start_line=current_start_line,
                         end_line=line_num - 1
                     )
                     current_chunk_lines = []
                     current_start_line = line_num
                     
                     if is_start:
                         current_name = is_start.group(1)
            
            current_chunk_lines.append(line)
            
            # If we matched a block start, update name for the *current* accumulating chunk
            if is_start and len(current_chunk_lines) == 1:
                current_name = is_start.group(1)

        # Yield remaining
        if current_chunk_lines:
            yield CodeChunk(
                chunk_id=self._make_id(rel_path, f"chunk_{current_start_line}"),
                file_path=rel_path,
                chunk_type="code_block",
                name=current_name,
                content="\n".join(current_chunk_lines),
                start_line=current_start_line,
                end_line=len(lines)
            )

    def _index_python_file(self, file_path: Path) -> Iterator[CodeChunk]:
        """Extract chunks from a single Python file using AST."""
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except (SyntaxError, UnicodeDecodeError) as e:
            logger.debug(f"Error parsing {file_path}: {e}")
            return
        
        rel_path = self._get_rel_path(file_path)
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
        covered_lines = set()
        if module_doc:
            covered_lines.update(range(1, self._get_docstring_end_line(tree) + 1))
        if imports:
            covered_lines.update(range(imports["start"], imports["end"] + 1))

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.stats.functions += 1
                chunk = self._chunk_from_function(node, rel_path, lines)
                covered_lines.update(range(chunk.start_line, chunk.end_line + 1))
                yield chunk
                
            elif isinstance(node, ast.ClassDef):
                self.stats.classes += 1
                # Yield class header
                chunk = self._chunk_from_class(node, rel_path, lines)
                # Note: header covered lines
                covered_lines.update(range(chunk.start_line, chunk.end_line + 1))
                yield chunk
                
                # Yield methods separately
                for method in node.body:
                    if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self.stats.methods += 1
                        m_chunk = self._chunk_from_function(
                            method, rel_path, lines, parent=node.name
                        )
                        covered_lines.update(range(m_chunk.start_line, m_chunk.end_line + 1))
                        yield m_chunk

        # 4. Fallback: Capture remaining top-level code as "script" chunks
        script_code_chunks = self._extract_script_chunks(tree, lines, covered_lines, rel_path)
        for chunk in script_code_chunks:
            self.stats.script_chunks += 1
            yield chunk
    
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

    def _extract_script_chunks(
        self, 
        tree: ast.Module, 
        lines: List[str], 
        covered_lines: Set[int],
        rel_path: str
    ) -> List[CodeChunk]:
        """Extract remaining top-level code as script chunks."""
        script_chunks = []
        
        # Collect all line ranges for non-indexed top-level nodes
        nodes_to_index = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, 
                                ast.Import, ast.ImportFrom)):
                continue
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                continue
            
            node_start = node.lineno
            node_end = node.end_lineno or node_start
            
            # Ensure it's not a node that was partially covered (rare but safe)
            if any(l in covered_lines for l in range(node_start, node_end + 1)):
                continue
                
            nodes_to_index.append((node_start, node_end))

        if not nodes_to_index:
            return []

        # Sort by start line
        nodes_to_index.sort()

        current_chunk_start = nodes_to_index[0][0]
        current_chunk_end = nodes_to_index[0][1]

        for i in range(1, len(nodes_to_index)):
            n_start, n_end = nodes_to_index[i]
            
            # If the gap between nodes contains any covered lines, we must split
            has_gap_covered = any(l in covered_lines for l in range(current_chunk_end + 1, n_start))
            
            if not has_gap_covered and n_start <= current_chunk_end + 5: # Small gap allowed
                current_chunk_end = n_end
            else:
                # Split
                script_chunks.append(self._create_script_chunk(
                    current_chunk_start, current_chunk_end, rel_path, lines
                ))
                current_chunk_start = n_start
                current_chunk_end = n_end

        # Last one
        script_chunks.append(self._create_script_chunk(
            current_chunk_start, current_chunk_end, rel_path, lines
        ))
            
        return script_chunks

    def _create_script_chunk(
        self, 
        start: int, 
        end: int, 
        rel_path: str, 
        lines: List[str]
    ) -> CodeChunk:
        """Helper to create a script chunk."""
        content = "\n".join(lines[start - 1:end])
        return CodeChunk(
            chunk_id=self._make_id(rel_path, f"script_{start}"),
            file_path=rel_path,
            chunk_type="script",
            name=f"script_L{start}",
            content=content,
            start_line=start,
            end_line=end,
            dependencies=[] # Could extract deps here too if needed
        )
    
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
