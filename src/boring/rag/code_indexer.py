"""
Universal Code Indexer for Vector RAG V11.0

Polyglot code chunking system supporting:
- Python (.py): AST-based parsing with dependency extraction
- JavaScript/TypeScript (.js/.jsx/.ts/.tsx): Tree-sitter with React component support
- Go (.go): Tree-sitter with method receiver extraction
- Rust (.rs), Java (.java): Tree-sitter semantic parsing
- C/C++ (.c/.cpp/.h/.hpp): Tree-sitter with namespace/template support
- Ruby (.rb), PHP (.php): Tree-sitter support
- Markdown (.md): Heading-based chunking

V11.0 Enhancements:
- Enhanced cross-language Tree-sitter precision
- Structured validation tests for JS/TS/Go/C++
- Interface and type alias detection
- Go method receiver tracking

Chunk Types:
- Function-level chunks with signature extraction
- Class-level chunks with inheritance tracking
- Interface and type alias chunks
- Import block chunks with dependency metadata
- Module docstrings and documentation

Uses Python AST for .py files and Tree-sitter for all other languages.
"""

import ast
import hashlib
import logging
import os
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class CodeChunk:
    """A semantic chunk of code for embedding."""

    chunk_id: str
    file_path: str
    chunk_type: str  # "function", "class", "imports", "module_doc", "interface", "type_alias"
    name: str
    content: str
    start_line: int
    end_line: int
    dependencies: list[str] = field(default_factory=list)  # Functions/classes this chunk calls
    parent: Optional[str] = None  # Parent class if method
    receiver: Optional[str] = None  # Go method receiver type (V11.0)
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

    SUPPORTED_EXTENSIONS: set[str] = {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".go",
        ".rs",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".java",
        ".md",
    }

    IGNORED_DIRS: set[str] = {
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        "htmlcov",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "dist",
        "build",
        "*.egg-info",
        ".boring_memory",
    }

    def __init__(
        self, project_root: Path, max_chunk_tokens: int = 500, include_init_files: bool = False
    ):
        self.project_root = Path(project_root)
        self.max_chunk_tokens = max_chunk_tokens
        self.include_init_files = include_init_files
        self.stats = IndexStats()

    def collect_files(self) -> list[Path]:
        """
        Collect all files that should be indexed.

        Returns:
            List of Path objects for all indexable files in the project.
        """
        files = []
        for root, dirs, filenames in os.walk(self.project_root):
            # Skip hidden directories and those in ignore list
            dirs[:] = [d for d in dirs if not self._should_skip_dir(d)]

            for filename in filenames:
                file_path = Path(root) / filename
                if self._should_skip_path(file_path):
                    continue
                files.append(file_path)
        return files

    def index_project(self) -> Iterator[CodeChunk]:
        """
        Index all supported files in the project.

        Yields:
            CodeChunk objects for each semantic unit
        """
        self.stats = IndexStats()

        for file_path in self.collect_files():
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
        return dir_name in self.IGNORED_DIRS or any(
            dir_name.endswith(ex[1:]) for ex in self.IGNORED_DIRS if ex.startswith("*")
        )

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

        V11.0: Enhanced to capture interface, type_alias, namespace, and Go method receivers.
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

        # 1. Try Tree-sitter Parsing (V11.0 Enhanced)
        if ts_parser and ts_parser.is_available():
            ts_chunks = ts_parser.parse_file(file_path)
            if ts_chunks:
                for chunk in ts_chunks:
                    # V11.0: Map parser chunk types to indexer chunk types
                    chunk_type_map = {
                        "function": "code_function",
                        "class": "code_class",
                        "method": "code_method",
                        "interface": "code_interface",
                        "type_alias": "code_type_alias",
                        "namespace": "code_namespace",
                    }
                    mapped_type = chunk_type_map.get(chunk.type, f"code_{chunk.type}")

                    yield CodeChunk(
                        chunk_id=self._make_id(rel_path, f"{chunk.type}_{chunk.name}"),
                        file_path=rel_path,
                        chunk_type=mapped_type,
                        name=chunk.name,
                        content=chunk.content,
                        start_line=chunk.start_line,
                        end_line=chunk.end_line,
                        receiver=getattr(chunk, "receiver", None),  # V11.0: Go method receiver
                    )
                # If we got chunks, assume we handled the file well enough (for now).
                # Optionally we could index the gaps as well, but definitions are key.
                return

        # 2. Fallback to Smart Regex Chunking (if Tree-sitter unavailable or unsupported language)
        lines = content.splitlines()

        # Regex patterns for common block starts
        # C/C++/Java/JS/TS/Go/Rust function/class definitions
        block_start = re.compile(
            r"^\s*(?:export\s+)?(?:public\s+|private\s+|protected\s+)?(?:async\s+)?(?:func|function|class|interface|struct|impl|const|let|var|type|def)\s+([a-zA-Z0-9_]+)"
        )
        # Markdown headers
        md_header = re.compile(r"^#{1,3}\s+(.+)")

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
                        end_line=line_num - 1,
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
                end_line=len(lines),
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
                docstring=module_doc,
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
                dependencies=imports["modules"],
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
        self, node: ast.FunctionDef, file_path: str, lines: list[str], parent: Optional[str] = None
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
        signature = "\n".join(lines[start : sig_end + 1])

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
            docstring=docstring,
        )

    def _chunk_from_class(self, node: ast.ClassDef, file_path: str, lines: list[str]) -> CodeChunk:
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
            docstring=ast.get_docstring(node),
        )

    def _extract_dependencies(self, node: ast.AST) -> list[str]:
        """Extract all function/method calls within a node."""
        deps: set[str] = set()

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                # Direct function call: func()
                if isinstance(child.func, ast.Name):
                    deps.add(child.func.id)
                # Method call: obj.method()
                elif isinstance(child.func, ast.Attribute):
                    deps.add(child.func.attr)

        # Filter out builtins and common functions
        builtins = {
            "print",
            "len",
            "str",
            "int",
            "float",
            "list",
            "dict",
            "set",
            "tuple",
            "range",
            "enumerate",
            "zip",
            "map",
            "filter",
            "open",
            "isinstance",
            "issubclass",
            "hasattr",
            "getattr",
            "setattr",
        }

        return sorted(deps - builtins)

    def _extract_imports(self, tree: ast.Module, lines: list[str]) -> Optional[dict]:
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
            "content": "\n".join(lines[start - 1 : end]),
            "start": start,
            "end": end,
            "modules": sorted(set(modules)),
        }

    def _extract_script_chunks(
        self, tree: ast.Module, lines: list[str], covered_lines: set[int], rel_path: str
    ) -> list[CodeChunk]:
        """Extract remaining top-level code as script chunks."""
        script_chunks = []

        # Collect all line ranges for non-indexed top-level nodes
        nodes_to_index = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom),
            ):
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

            if not has_gap_covered and n_start <= current_chunk_end + 5:  # Small gap allowed
                current_chunk_end = n_end
            else:
                # Split
                script_chunks.append(
                    self._create_script_chunk(
                        current_chunk_start, current_chunk_end, rel_path, lines
                    )
                )
                current_chunk_start = n_start
                current_chunk_end = n_end

        # Last one
        script_chunks.append(
            self._create_script_chunk(current_chunk_start, current_chunk_end, rel_path, lines)
        )

        return script_chunks

    def _create_script_chunk(
        self, start: int, end: int, rel_path: str, lines: list[str]
    ) -> CodeChunk:
        """Helper to create a script chunk."""
        content = "\n".join(lines[start - 1 : end])
        return CodeChunk(
            chunk_id=self._make_id(rel_path, f"script_{start}"),
            file_path=rel_path,
            chunk_type="script",
            name=f"script_L{start}",
            content=content,
            start_line=start,
            end_line=end,
            dependencies=[],  # Could extract deps here too if needed
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
        # Use sha256 for ID generation (non-security) to satisfy bandit
        return hashlib.sha256(raw.encode()).hexdigest()[:12]

    def get_stats(self) -> IndexStats:
        """Return indexing statistics."""
        return self.stats


# =============================================================================
# V11.0 Structured Validation Tests
# V11.1: Fixed JavaScript test cases (removed JSX, use pure JS syntax)
# =============================================================================


class CrossLanguageValidator:
    """
    V11.0: Structured tests for cross-language Tree-sitter precision.
    V11.1: Fixed JavaScript test cases to use valid non-JSX syntax.

    Ensures boring_rag_context works correctly for JS/TS/Go/C++.
    """

    # Test cases for each language
    TEST_CASES = {
        "javascript": {
            "code": """
// Regular function
function handleClick(event) {
    console.log("clicked");
}

// Arrow function component (without JSX for pure JS parsing)
const Button = ({ label }) => {
    return document.createElement("button");
};

// Anonymous function expression
const myHelper = function(x) {
    return x * 2;
};

// Class component
class Counter {
    constructor() {
        this.count = 0;
    }
    render() {
        return this.count;
    }
}

// Export function
export function App() {
    return "app";
}
""",
            "expected_names": ["handleClick", "Button", "myHelper", "Counter", "App", "render"],
            "expected_types": ["function", "class", "method"],
        },
        "typescript": {
            "code": """
// Interface
interface User {
    id: number;
    name: string;
}

// Type alias
type UserID = string | number;

// Typed arrow function
const fetchUser: (id: UserID) => Promise<User> = async (id) => {
    return { id: 1, name: "test" };
};

// Class with interface
class UserService implements IService {
    getUser(id: number): User {
        return { id, name: "test" };
    }
}

// Enum
enum Status {
    Active,
    Inactive
}
""",
            "expected_names": ["User", "UserID", "fetchUser", "UserService", "Status"],
            "expected_types": ["interface", "type_alias", "function", "class"],
        },
        "go": {
            "code": """
package main

// Regular function
func HandleRequest(w http.ResponseWriter, r *http.Request) {
    fmt.Println("handling")
}

// Struct type
type User struct {
    ID   int
    Name string
}

// Method with pointer receiver
func (u *User) GetName() string {
    return u.Name
}

// Method with value receiver
func (u User) String() string {
    return u.Name
}

// Interface
type Repository interface {
    Find(id int) (*User, error)
}
""",
            "expected_names": ["HandleRequest", "User", "GetName", "String", "Repository"],
            "expected_types": ["function", "method", "class", "interface"],
        },
        "cpp": {
            "code": """
// Namespace
namespace MyApp {

// Class
class Calculator {
public:
    int add(int a, int b);
};

// Template function
template<typename T>
T maximum(T a, T b) {
    return (a > b) ? a : b;
}

// Struct
struct Point {
    int x, y;
};

} // namespace MyApp

// Regular function
int main() {
    return 0;
}
""",
            "expected_names": ["MyApp", "Calculator", "maximum", "Point", "main"],
            "expected_types": ["namespace", "class", "function"],
        },
    }

    @classmethod
    def validate_language(cls, language: str) -> dict:
        """
        Validate Tree-sitter parsing for a specific language.

        Args:
            language: Language to validate (javascript, typescript, go, cpp)

        Returns:
            Validation result dict
        """
        try:
            from .parser import TreeSitterParser

            parser = TreeSitterParser()
        except ImportError:
            return {"success": False, "error": "TreeSitterParser not available"}

        if language not in cls.TEST_CASES:
            return {"success": False, "error": f"No test case for language: {language}"}

        test_case = cls.TEST_CASES[language]
        result = parser.validate_language_support(language, test_case["code"])

        if not result.get("success"):
            return result

        # Check expected names
        found_names = set(result.get("chunk_names", []))
        expected_names = set(test_case["expected_names"])
        missing_names = expected_names - found_names

        # Check expected types
        found_types = set(result.get("chunk_types", []))
        expected_types = set(test_case["expected_types"])
        missing_types = expected_types - found_types

        return {
            "success": len(missing_names) == 0,
            "language": language,
            "chunks_found": result.get("chunks_found", 0),
            "found_names": list(found_names),
            "missing_names": list(missing_names),
            "found_types": list(found_types),
            "missing_types": list(missing_types),
            "receivers": result.get("receivers", []),
        }

    @classmethod
    def validate_all(cls) -> dict:
        """
        Validate all supported languages.

        Returns:
            Dict with validation results for each language
        """
        results = {}
        all_passed = True

        for language in cls.TEST_CASES:
            result = cls.validate_language(language)
            results[language] = result
            if not result.get("success"):
                all_passed = False

        return {
            "all_passed": all_passed,
            "results": results,
        }
