"""
Tree-sitter Parser Wrapper

Provides a unified interface to parse code and extract semantic chunks (functions, classes)
using tree-sitter-languages.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from tree_sitter_languages import get_language, get_parser

    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False
    logger.warning("tree-sitter-languages not installed. Advanced parsing disabled.")


@dataclass
class ParsedChunk:
    """A semantic chunk of code."""

    type: str  # 'function', 'class', 'method'
    name: str
    start_line: int  # 1-indexed
    end_line: int  # 1-indexed
    content: str


class TreeSitterParser:
    """Wrapper for tree-sitter parsing."""

    # File extension to language name mapping
    EXT_TO_LANG = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".go": "go",
        ".java": "java",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".c": "c",
        ".h": "c",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
    }

    # S-expression queries for extracting definitions
    # Note: These are simplified common queries.
    QUERIES = {
        "python": """
            (function_definition
                name: (identifier) @name) @function
            (class_definition
                name: (identifier) @name) @class
        """,
        "javascript": """
            (function_declaration
                name: (identifier) @name) @function
            (class_declaration
                name: (identifier) @name) @class
            (method_definition
                name: (property_identifier) @name) @method
            (variable_declarator
                name: (identifier) @name
                value: [(arrow_function) (function_expression)]
            ) @function
        """,
        "typescript": """
            (function_declaration
                name: (identifier) @name) @function
            (class_declaration
                name: (type_identifier) @name) @class
            (method_definition
                name: (property_identifier) @name) @method
            (interface_declaration
                name: (type_identifier) @name) @class
        """,
        "go": """
            (function_declaration
                name: (identifier) @name) @function
            (method_declaration
                name: (field_identifier) @name) @function
            (type_declaration
                (type_spec
                    name: (type_identifier) @name)) @class
        """,
        "java": """
            (method_declaration
                name: (identifier) @name) @function
            (class_declaration
                name: (identifier) @name) @class
            (interface_declaration
                name: (identifier) @name) @class
        """,
        "cpp": """
            (function_definition
                declarator: (function_declarator
                    declarator: (identifier) @name)) @function
            (class_specifier
                name: (type_identifier) @name) @class
        """,
        "rust": """
            (function_item
                name: (identifier) @name) @function
            (impl_item
                type: (type_identifier) @name) @class
            (struct_item
                name: (type_identifier) @name) @class
        """,
        "ruby": """
            (method
                name: (identifier) @name) @function
            (class
                name: (constant) @name) @class
            (module
                name: (constant) @name) @class
            (singleton_method
                name: (identifier) @name) @function
        """,
        "php": """
            (function_definition
                name: (name) @name) @function
            (class_declaration
                name: (name) @name) @class
            (method_declaration
                name: (name) @name) @method
            (interface_declaration
                name: (name) @name) @class
        """,
    }

    def __init__(self):
        self.parsers = {}

    def is_available(self) -> bool:
        """Check if tree-sitter is available."""
        return HAS_TREE_SITTER

    def get_language_for_file(self, file_path: Path) -> Optional[str]:
        """Determine language from file extension."""
        return self.EXT_TO_LANG.get(file_path.suffix.lower())

    def parse_file(self, file_path: Path) -> list[ParsedChunk]:
        """
        Parse a file and extract semantic chunks.
        Returns empty list if language not supported or parser fails.
        """
        if not HAS_TREE_SITTER:
            return []

        lang_name = self.get_language_for_file(file_path)
        if not lang_name:
            return []

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to read file {file_path}: {e}")
            return []

        return self.extract_chunks(content, lang_name)

    def extract_chunks(self, code: str, language: str) -> list[ParsedChunk]:
        """Extract chunks from code string using tree-sitter."""
        if not HAS_TREE_SITTER:
            return []

        try:
            # Lazy load parser
            if language not in self.parsers:
                self.parsers[language] = get_parser(language)

            parser = self.parsers[language]
            tree = parser.parse(bytes(code, "utf8"))

            query_str = self.QUERIES.get(language)
            if not query_str:
                return []

            ts_language = get_language(language)
            query = ts_language.query(query_str)

            chunks = []
            captures = query.captures(tree.root_node)

            # captures is a list of (Node, str_capture_name)
            # We need to pair @function/@class with its inner @name
            # This is tricky because captures are flattened.
            # Simplified approach: Iterate nodes, check type.

            # Better approach: Iterate matches if query.matches returns them?
            # tree-sitter-languages bindings vary.
            # Let's try standard capture iteration processing.

            # We will store potential chunks keyed by node id to merge name + body
            pending_nodes = {}

            for node, name in captures:
                if name in ["function", "class", "method"]:
                    pending_nodes[node.id] = {"node": node, "type": name, "name": "anonymous"}
                elif name == "name":
                    # The name usually belongs to the immediate parent or grandparent
                    # dependent on the grammar structure.
                    # We look up the ancestry.
                    curr = node.parent
                    while curr:
                        if curr.id in pending_nodes:
                            pending_nodes[curr.id]["name"] = code[node.start_byte : node.end_byte]
                            break
                        curr = curr.parent

            # Convert to ParsedChunk objects
            code.splitlines()

            for item in pending_nodes.values():
                node = item["node"]
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1

                # Extract text
                # We can index into 'lines' or use byte offsets if we have the bytes
                chunk_content = node.text.decode("utf8")

                chunks.append(
                    ParsedChunk(
                        type=item["type"],
                        name=item["name"],
                        start_line=start_line,
                        end_line=end_line,
                        content=chunk_content,
                    )
                )

            return sorted(chunks, key=lambda x: x.start_line)

        except Exception as e:
            logger.error(f"Tree-sitter parse error for {language}: {e}")
            return []
