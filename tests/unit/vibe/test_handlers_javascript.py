"""
Tests for JavaScript/TypeScript handler.
"""

import pytest

from boring.vibe.handlers.javascript import JavascriptHandler


class TestJavascriptHandler:
    """Tests for JavascriptHandler."""

    @pytest.fixture
    def handler(self):
        return JavascriptHandler()

    def test_supported_extensions(self, handler):
        """Test supported extensions."""
        assert ".js" in handler.supported_extensions
        assert ".jsx" in handler.supported_extensions
        assert ".ts" in handler.supported_extensions
        assert ".tsx" in handler.supported_extensions

    def test_language_name(self, handler):
        """Test language name."""
        assert handler.language_name == "JavaScript/TypeScript"

    def test_analyze_for_test_gen_export_function(self, handler):
        """Test analyzing exported functions."""
        code = """
export function add(a, b) {
    return a + b;
}

export async function fetchData(url) {
    return await fetch(url);
}
"""
        result = handler.analyze_for_test_gen("test.js", code)
        assert len(result.functions) == 2
        assert result.functions[0].name == "add"
        assert result.functions[1].name == "fetchData"
        assert result.functions[1].is_async is True

    def test_analyze_for_test_gen_arrow_function(self, handler):
        """Test analyzing arrow functions."""
        code = """
export const multiply = (a, b) => a * b;
export const asyncTask = async (data) => await process(data);
"""
        result = handler.analyze_for_test_gen("test.js", code)
        assert len(result.functions) >= 2
        assert any(f.name == "multiply" for f in result.functions)

    def test_analyze_for_test_gen_class(self, handler):
        """Test analyzing exported classes."""
        code = """
export class Calculator {
    add(a, b) { return a + b; }
}
"""
        result = handler.analyze_for_test_gen("test.js", code)
        assert len(result.classes) == 1
        assert result.classes[0].name == "Calculator"

    def test_perform_code_review_error_handling(self, handler):
        """Test code review for error handling."""
        code = """
try {
    risky();
} catch {}
"""
        result = handler.perform_code_review("test.js", code, focus="error_handling")
        assert len(result.issues) > 0
        assert any("Empty catch" in issue.message for issue in result.issues)

    def test_perform_code_review_performance(self, handler):
        """Test code review for performance issues."""
        code = """
for (let i = 0; i < items.length; i++) {
    await process(items[i]);
}
"""
        result = handler.perform_code_review("test.js", code, focus="performance")
        assert len(result.issues) > 0
        assert any("await" in issue.message.lower() for issue in result.issues)

    def test_perform_code_review_security(self, handler):
        """Test code review for security issues."""
        code = """
const result = eval(userInput);
element.innerHTML = userContent;
"""
        result = handler.perform_code_review("test.js", code, focus="security")
        assert len(result.issues) > 0
        assert any("eval" in issue.message.lower() for issue in result.issues)

    def test_generate_test_code(self, handler):
        """Test test code generation."""
        from boring.vibe.analysis import CodeClass, CodeFunction, TestGenResult

        result = TestGenResult(
            file_path="math.js",
            functions=[CodeFunction(name="add", args=["a", "b"], docstring=None, lineno=1)],
            classes=[CodeClass(name="Calculator", methods=["add"], docstring=None, lineno=5)],
            module_name="math",
            source_language="javascript",
        )
        test_code = handler.generate_test_code(result, "/project")
        assert "describe" in test_code
        assert "add" in test_code
        assert "Calculator" in test_code

    def test_extract_dependencies(self, handler):
        """Test dependency extraction."""
        code = """
import { foo } from './utils';
const bar = require('lodash');
const baz = await import('./async-module');
"""
        deps = handler.extract_dependencies("test.js", code)
        assert "./utils" in deps
        assert "lodash" in deps
        assert "./async-module" in deps

    def test_extract_documentation(self, handler):
        """Test documentation extraction."""
        code = """
/**
 * Adds two numbers.
 * @param {number} a - First number
 * @param {number} b - Second number
 * @returns {number} Sum
 */
export function add(a, b) {
    return a + b;
}
"""
        result = handler.extract_documentation("test.js", code)
        assert len(result.items) > 0
        assert any(item.name == "add" for item in result.items)
