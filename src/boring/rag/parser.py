"""
Tree-sitter Parser Wrapper V11.0

Provides a unified interface to parse code and extract semantic chunks (functions, classes)
using tree-sitter-languages.

V11.0 Enhancements:
- Enhanced JavaScript/TypeScript queries for React components and arrow functions
- Go method receiver support with full receiver type extraction
- TypeScript interface and type alias support
- C++ namespace and template support
- Structured validation for cross-language precision
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

import sys

try:
    from tree_sitter_languages import get_language, get_parser

    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False
    logger.warning(
        f"tree-sitter-languages not installed in {sys.executable}. Advanced parsing disabled."
    )


@dataclass
class ParsedChunk:
    """A semantic chunk of code."""

    type: str  # 'function', 'class', 'method', 'interface', 'type_alias', 'component'
    name: str
    start_line: int  # 1-indexed
    end_line: int  # 1-indexed
    content: str
    receiver: Optional[str] = None  # For Go method receivers
    signature: Optional[str] = None  # Function/method signature


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
    # V11.0: Enhanced queries for cross-language precision
    # V11.1: Fixed JavaScript function_expression -> function node type
    QUERIES = {
        "python": """
            (function_definition
                name: (identifier) @name) @function
            (class_definition
                name: (identifier) @name) @class
            (decorated_definition
                definition: (function_definition
                    name: (identifier) @name)) @function
        """,
        "javascript": """
            ; Regular function declarations
            (function_declaration
                name: (identifier) @name) @function

            ; Class declarations
            (class_declaration
                name: (identifier) @name) @class

            ; Method definitions in classes
            (method_definition
                name: (property_identifier) @name) @method

            ; Arrow functions assigned to variables (React components pattern)
            (variable_declarator
                (identifier) @name
                (arrow_function)) @function

            ; Anonymous function expressions assigned to variables
            ; Note: In tree-sitter-languages, the node type is 'function' not 'function_expression'
            (variable_declarator
                (identifier) @name
                (function)) @function

            ; Export statement with function declaration
            (export_statement
                (function_declaration
                    name: (identifier) @name)) @function

            ; React.memo, React.forwardRef wrapped components
            (variable_declarator
                (identifier) @name
                (call_expression
                    (member_expression))) @function
        """,
        "typescript": """
            ; Function declarations
            (function_declaration
                name: (identifier) @name) @function

            ; Class declarations
            (class_declaration
                name: (type_identifier) @name) @class

            ; Interface declarations (V11.0 enhancement)
            (interface_declaration
                name: (type_identifier) @name) @interface

            ; Type alias declarations (V11.0 enhancement)
            (type_alias_declaration
                name: (type_identifier) @name) @type_alias

            ; Method definitions
            (method_definition
                name: (property_identifier) @name) @method

            ; Arrow functions (including React FC components)
            (variable_declarator
                name: (identifier) @name
                value: (arrow_function)) @function

            ; Typed arrow functions: const Component: React.FC = () => {}
            (lexical_declaration
                (variable_declarator
                    name: (identifier) @name
                    type: (type_annotation)
                    value: (arrow_function))) @function

            ; Export default function
            (export_statement
                declaration: (function_declaration
                    name: (identifier) @name)) @function

            ; Enum declarations
            (enum_declaration
                name: (identifier) @name) @class

            ; Abstract class
            (abstract_class_declaration
                name: (type_identifier) @name) @class
        """,
        "go": """
            ; Regular function declarations
            (function_declaration
                name: (identifier) @name) @function

            ; Method declarations with receiver (V11.0 enhancement)
            ; Captures both the method name and receiver type
            (method_declaration
                receiver: (parameter_list
                    (parameter_declaration
                        type: (_) @receiver_type))
                name: (field_identifier) @name) @method

            ; Type declarations (struct, interface)
            (type_declaration
                (type_spec
                    name: (type_identifier) @name)) @class

            ; Interface type specifically
            (type_declaration
                (type_spec
                    name: (type_identifier) @name
                    type: (interface_type))) @interface
        """,
        "java": """
            (method_declaration
                name: (identifier) @name) @function
            (class_declaration
                name: (identifier) @name) @class
            (interface_declaration
                name: (identifier) @name) @interface
            (constructor_declaration
                name: (identifier) @name) @function
            (enum_declaration
                name: (identifier) @name) @class
            (annotation_type_declaration
                name: (identifier) @name) @class
        """,
        "cpp": """
            ; Function definitions
            (function_definition
                declarator: (function_declarator
                    declarator: (identifier) @name)) @function

            ; Class specifiers
            (class_specifier
                name: (type_identifier) @name) @class

            ; Struct specifiers
            (struct_specifier
                name: (type_identifier) @name) @class

            ; Namespace definitions (V11.0 enhancement)
            (namespace_definition
                name: (namespace_identifier) @name) @namespace

            ; Template declarations (V11.0 enhancement)
            (template_declaration
                (function_definition
                    declarator: (function_declarator
                        declarator: (identifier) @name))) @function

            ; Template class
            (template_declaration
                (class_specifier
                    name: (type_identifier) @name)) @class
        """,
        "c": """
            (function_definition
                declarator: (function_declarator
                    declarator: (identifier) @name)) @function
            (struct_specifier
                name: (type_identifier) @name) @class
            (enum_specifier
                name: (type_identifier) @name) @class
            (type_definition
                declarator: (type_identifier) @name) @type_alias
        """,
        "rust": """
            (function_item
                name: (identifier) @name) @function
            (impl_item
                type: (type_identifier) @name) @class
            (struct_item
                name: (type_identifier) @name) @class
            (enum_item
                name: (type_identifier) @name) @class
            (trait_item
                name: (type_identifier) @name) @interface
            (type_item
                name: (type_identifier) @name) @type_alias
            (mod_item
                name: (identifier) @name) @namespace
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
                name: (name) @name) @interface
            (trait_declaration
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
        """
        Extract chunks from code string using tree-sitter.

        V11.0: Enhanced to handle interface, type_alias, namespace, and Go method receivers.
        """
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

            chunk_types = {
                "function",
                "class",
                "method",
                "interface",
                "type_alias",
                "namespace",
            }

            # V11.1: Type specificity ranking - more specific types take precedence
            # Higher number = more specific
            type_specificity = {
                "class": 1,
                "function": 2,
                "method": 3,
                "namespace": 4,
                "type_alias": 5,
                "interface": 6,  # interface is more specific than class for Go
            }

            result = []
            matches = query.matches(tree.root_node)

            # Map of node_id -> dict to avoid duplicates if multiple queries hit the same node
            processed_chunks = {}

            for _match_id, captures in matches:
                # In 0.21.3, captures is a dict mapping capture_name -> Node
                # (or list of Nodes depending on configuration, but usually Node for matches)

                # Identify the primary chunk node in this match
                chunk_node = None
                chunk_type = None
                for c_name, node in captures.items():
                    if c_name in chunk_types:
                        chunk_node = node
                        chunk_type = c_name
                        break

                if not chunk_node:
                    continue

                # Get or create the chunk entry
                node_id = chunk_node.id

                # V11.1: Check if this type is more specific than existing one
                if node_id in processed_chunks:
                    existing_type = processed_chunks[node_id]["type"]
                    existing_specificity = type_specificity.get(existing_type, 0)
                    new_specificity = type_specificity.get(chunk_type, 0)
                    if new_specificity > existing_specificity:
                        # Update to more specific type
                        processed_chunks[node_id]["type"] = chunk_type
                else:
                    start_line = chunk_node.start_point[0] + 1
                    end_line = chunk_node.end_point[0] + 1
                    content = chunk_node.text.decode("utf8")
                    lines = content.split("\n")
                    signature = lines[0] if lines else ""

                    # Capture signature spanning multiple lines
                    if "{" not in signature and len(lines) > 1:
                        for i, line in enumerate(lines[1:], 1):
                            signature += "\n" + line
                            if "{" in line or i >= 3:
                                break

                    processed_chunks[node_id] = {
                        "type": chunk_type,
                        "name": "anonymous",
                        "start_line": start_line,
                        "end_line": end_line,
                        "content": content,
                        "signature": signature.strip(),
                        "receiver": None,
                    }

                # Extract attributes from the same match
                chunk_data = processed_chunks[node_id]

                # Defensive capture name lookup
                capture_names = {
                    query.capture_names[k]: node
                    for k, node in captures.items()
                    if isinstance(k, int)
                }
                capture_names.update(
                    {k: node for k, node in captures.items() if isinstance(k, str)}
                )

                if "name" in capture_names:
                    name_node = capture_names["name"]
                    chunk_data["name"] = name_node.text.decode("utf8")

                if "receiver_type" in capture_names:
                    recv_node = capture_names["receiver_type"]
                    recv_text = recv_node.text.decode("utf8")
                    if recv_text.startswith("*"):
                        recv_text = recv_text[1:]
                    chunk_data["receiver"] = recv_text

            # Sort and return
            for data in processed_chunks.values():
                result.append(ParsedChunk(**data))

            return sorted(result, key=lambda x: x.start_line)

        except Exception as e:
            logger.error(f"Tree-sitter match failure for {language}: {e}")
            return []

    def validate_language_support(self, language: str, test_code: str) -> dict:
        """
        Validate that Tree-sitter queries work correctly for a given language.

        V11.0: Structured testing for cross-language precision.

        Args:
            language: Language name (e.g., 'go', 'typescript')
            test_code: Sample code to parse

        Returns:
            Dict with validation results
        """
        if not HAS_TREE_SITTER:
            return {"success": False, "error": "tree-sitter not available"}

        if language not in self.QUERIES:
            return {"success": False, "error": f"No query defined for language: {language}"}

        try:
            chunks = self.extract_chunks(test_code, language)
            return {
                "success": True,
                "language": language,
                "chunks_found": len(chunks),
                "chunk_types": list({c.type for c in chunks}),
                "chunk_names": [c.name for c in chunks],
                "receivers": [c.receiver for c in chunks if c.receiver],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
