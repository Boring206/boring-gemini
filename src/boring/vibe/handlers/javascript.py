# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
JavaScript/TypeScript Language Handler.

Implements analysis using Regex (since we don't have a JS AST parser in Python stdlib).
"""

import re

from ..analysis import (
    CodeClass,
    CodeFunction,
    CodeIssue,
    DocItem,
    DocResult,
    ReviewResult,
    TestGenResult,
)
from .base import BaseHandler


class JavascriptHandler(BaseHandler):
    """Handler for JS/TS files using Regex."""

    @property
    def supported_extensions(self) -> list[str]:
        return [".js", ".jsx", ".ts", ".tsx"]

    @property
    def language_name(self) -> str:
        return "JavaScript/TypeScript"

    def analyze_for_test_gen(self, file_path: str, source_code: str) -> TestGenResult:
        """Extract exported functions and classes using Regex."""
        functions = []
        classes = []

        # Regex patterns for exports
        # export function foo(...)
        # export const foo = (...) =>
        # export default function foo(...)

        # 1. Exported Functions: export function name(...)
        func_pattern = re.compile(
            r"export\s+(?:async\s+)?function\s+(\w+)\s*\((.*?)\)", re.MULTILINE
        )
        for match in func_pattern.finditer(source_code):
            name, args = match.groups()
            functions.append(
                CodeFunction(
                    name=name,
                    args=[a.strip() for a in args.split(",") if a.strip()],
                    docstring=None,
                    lineno=source_code[: match.start()].count("\n") + 1,
                    is_async="async" in match.group(0),
                    is_exported=True,
                )
            )

        # 2. Exported Arrow Functions: export const name = (...) =>
        arrow_pattern = re.compile(
            r"export\s+const\s+(\w+)\s*=\s*(?:async\s+)?\(?(.*?)\)?\s*=>", re.MULTILINE
        )
        for match in arrow_pattern.finditer(source_code):
            name, args = match.groups()
            functions.append(
                CodeFunction(
                    name=name,
                    args=[a.strip() for a in args.split(",") if a.strip()],
                    docstring=None,
                    lineno=source_code[: match.start()].count("\n") + 1,
                    is_async="async" in match.group(0),
                    is_exported=True,
                )
            )

        # 3. Exported Classes: export class Name
        class_pattern = re.compile(r"export\s+class\s+(\w+)", re.MULTILINE)
        for match in class_pattern.finditer(source_code):
            name = match.group(1)
            # Simple heuristic for methods: scan until next class or end
            # This is limited in regex, usually we just assume empty methods for now or basic scan
            classes.append(
                CodeClass(
                    name=name,
                    methods=["constructor"],  # Placeholder
                    docstring=None,
                    lineno=source_code[: match.start()].count("\n") + 1,
                    is_exported=True,
                )
            )

        return TestGenResult(
            file_path=file_path,
            functions=functions,
            classes=classes,
            module_name=file_path.split("/")[-1].split(".")[0],
            source_language="typescript"
            if file_path.endswith("ts") or file_path.endswith("tsx")
            else "javascript",
        )

    def perform_code_review(
        self, file_path: str, source_code: str, focus: str = "all"
    ) -> ReviewResult:
        """Perform Regex-based code review with simple state machine."""
        issues = []

        lines = source_code.split("\n")

        # State tracking
        brace_depth = 0
        loop_scopes = []  # Stack of depths where loops are active

        # Simple loop keywords
        loop_patterns = ["for ", "while ", ".map(", ".forEach(", ".filter(", ".reduce("]

        for i, line in enumerate(lines, 1):
            line.strip()

            # 1. Update State (Start of line check)
            # Check if this line starts a loop
            is_loop_start = any(p in line for p in loop_patterns)

            # If we are starting a loop and it has an opening brace, record the SCOPE depth
            # Scope depth is (current brace_depth + 1) because the code inside will be at that depth
            if is_loop_start:
                # Limitation: If { is on next line, this heuristic might miss strict scope tracking
                # But we assume standard JS formatting 'for (...) {'
                loop_scopes.append(brace_depth + 1)

            # Check if currently in loop
            # We are in a loop if current brace_depth >= any active loop scope start depth
            # AND the loop scope hasn't been closed (which we check at end of line)
            in_loop = any(brace_depth >= scope for scope in loop_scopes)

            # --- CHECKS ---

            # 1. Naming (CamelCase check) - Skip for now to avoid noise

            # 2. Error Handling
            if focus in ("all", "error_handling"):
                if "catch" in line and "{" in line and "}" in line and len(line) < 30:
                    issues.append(
                        CodeIssue(
                            category="Error Handling",
                            severity="medium",
                            message="Empty catch block?",
                            line=i,
                            suggestion="Log the error",
                        )
                    )

            # 3. Performance
            if focus in ("all", "performance"):
                # Await in loop
                if in_loop and "await " in line:
                    issues.append(
                        CodeIssue(
                            category="Performance",
                            severity="medium",
                            message="`await` inside loop",
                            line=i,
                            suggestion="Use `Promise.all()`",
                        )
                    )

                # DOM in loop
                if in_loop and (
                    "document.getElementById" in line or "document.querySelector" in line
                ):
                    issues.append(
                        CodeIssue(
                            category="Performance",
                            severity="high",
                            message="DOM access inside loop",
                            line=i,
                            suggestion="Cache DOM element outside loop",
                        )
                    )

                # General Performance
                if "console.log" in line:
                    issues.append(
                        CodeIssue(
                            category="Performance",
                            severity="low",
                            message="`console.log` found",
                            line=i,
                            suggestion="Remove in production",
                        )
                    )
                if "forceUpdate" in line:
                    issues.append(
                        CodeIssue(
                            category="Performance",
                            severity="high",
                            message="Using `forceUpdate`",
                            line=i,
                            suggestion="Avoid forcing re-renders",
                        )
                    )

            # 4. Security
            if focus in ("all", "security"):
                if "eval(" in line:
                    issues.append(
                        CodeIssue(
                            category="Security", severity="high", message="Avoid `eval()`", line=i
                        )
                    )
                if "innerHTML" in line:
                    issues.append(
                        CodeIssue(
                            category="Security",
                            severity="medium",
                            message="Unsafe `innerHTML`",
                            line=i,
                            suggestion="Use `textContent`",
                        )
                    )

            # --- Update State (End of line check) ---
            # Count braces to update depth
            open_braces = line.count("{")
            close_braces = line.count("}")

            # If we are closing braces, we might be closing loop scopes
            # A loop scope at depth D ends when brace_depth drops below D
            brace_depth += open_braces - close_braces

            # Prune closed, unreachable loop scopes
            loop_scopes = [s for s in loop_scopes if s <= brace_depth]

        return ReviewResult(file_path=file_path, issues=issues)

    def generate_test_code(self, result: TestGenResult, project_root: str) -> str:
        """Generate Jest/Vitest code."""
        # Calculate import path
        import_path = f"./{result.module_name}"

        lines = [
            "// Auto-generated by Vibe Coder Pro (boring_test_gen)",
            "// Run: npm test",
            "",
            f"import {{ {', '.join([f.name for f in result.functions] + [c.name for c in result.classes])} }} from '{import_path}';",
            "",
            "describe('Generated Tests', () => {",
        ]

        for func in result.functions:
            lines.append(f"  describe('{func.name}', () => {{")
            lines.append(
                f"    it('should work correctly', {'async ' if func.is_async else ''}() => {{"
            )
            lines.append(f"      // TODO: Test {func.name}")
            lines.append(
                f"      // const result = {'await ' if func.is_async else ''}{func.name}(...);"
            )
            lines.append("      // expect(result).toBeDefined();")
            lines.append("    });")
            lines.append("  });")
            lines.append("")

        for cls in result.classes:
            lines.append(f"  describe('{cls.name}', () => {{")
            lines.append("    it('should be instantiable', () => {")
            lines.append(f"      const instance = new {cls.name}();")
            lines.append("      expect(instance).toBeDefined();")
            lines.append("    });")
            lines.append("  });")
            lines.append("")

        lines.append("});")
        return "\n".join(lines)

    def extract_dependencies(self, file_path: str, source_code: str) -> list[str]:
        """Extract imports/requires using Regex."""
        imports = []

        # 1. import ... from '...'
        # pattern: import .* from ['"](.*)['"]
        import_pattern = re.compile(r"import\s+.*?from\s+['\"](.*?)['\"]", re.MULTILINE)
        for match in import_pattern.finditer(source_code):
            imports.append(match.group(1))

        # 2. require('...')
        # pattern: require\(['"](.*)['"]\)
        require_pattern = re.compile(r"require\s*\(\s*['\"](.*?)['\"]\s*\)", re.MULTILINE)
        for match in require_pattern.finditer(source_code):
            imports.append(match.group(1))

        # 3. Dynamic import('...')
        dyn_import_pattern = re.compile(r"import\s*\(\s*['\"](.*?)['\"]\s*\)", re.MULTILINE)
        for match in dyn_import_pattern.finditer(source_code):
            imports.append(match.group(1))

        return sorted(set(imports))

    def extract_documentation(self, file_path: str, source_code: str) -> DocResult:
        """Extract JSDoc comments using regex."""
        items = []

        # Regex for JSDoc followed by function/class
        # Captures: 1=DocContent, 2=DeclarationType, 3=Name
        pattern = re.compile(
            r"/\*\*([\s\S]*?)\*/\s*"  # Match JSDoc block
            r"(?:export\s+)?(?:default\s+)?"  # Optional export/default
            r"(?:async\s+)?"  # Optional async
            r"(function|class|const|let|var)\s+"  # Type
            r"([a-zA-Z0-9_]+)",  # Name
            re.MULTILINE,
        )

        for match in pattern.finditer(source_code):
            doc_content = match.group(1).strip()
            decl_type = match.group(2)
            name = match.group(3)

            # Simple signature approximation
            signature = f"{decl_type} {name}"

            # Refine type
            item_type = "function" if decl_type in ("function", "const", "let", "var") else "class"
            if (
                decl_type in ("const", "let", "var")
                and "=>" not in source_code[match.end() : match.end() + 50]
            ):
                # Might be a variable, not a function, strictly speaking.
                # But Vibe Coder usually cares about logic.
                # For now treat valid JSDoc'd consts as worth documenting.
                item_type = "variable"

            # Clean doc lines
            clean_doc = "\n".join(
                line.strip().lstrip("*").strip() for line in doc_content.splitlines()
            )

            items.append(
                DocItem(
                    name=name,
                    type=item_type,
                    docstring=clean_doc,
                    signature=signature,
                    line_number=source_code[: match.start()].count("\n") + 1,
                )
            )

        return DocResult(
            file_path=file_path,
            module_doc="",  # JS logic for module doc is fuzzy (first comment?)
            items=items,
        )
