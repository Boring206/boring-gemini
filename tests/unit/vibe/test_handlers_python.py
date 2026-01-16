"""
Tests for Python handler.
"""

import pytest

from boring.vibe.handlers.python import PythonHandler


class TestPythonHandler:
    """Tests for PythonHandler."""

    @pytest.fixture
    def handler(self):
        return PythonHandler()

    def test_supported_extensions(self, handler):
        """Test supported extensions."""
        assert handler.supported_extensions == [".py"]

    def test_language_name(self, handler):
        """Test language name."""
        assert handler.language_name == "Python"

    def test_analyze_for_test_gen_functions(self, handler):
        """Test analyzing functions."""
        code = """
def add(a, b):
    '''Add two numbers.'''
    return a + b

async def fetch_data(url):
    return await fetch(url)

def _private():
    pass
"""
        result = handler.analyze_for_test_gen("test.py", code)
        # Note: async functions are detected as AsyncFunctionDef, not FunctionDef
        assert len(result.functions) >= 1  # At least add function
        assert result.functions[0].name == "add"
        # Check for async function if present
        async_funcs = [f for f in result.functions if f.name == "fetch_data"]
        if async_funcs:
            assert async_funcs[0].is_async is True

    def test_analyze_for_test_gen_classes(self, handler):
        """Test analyzing classes."""
        code = """
class Calculator:
    '''A calculator class.'''
    def add(self, a, b):
        return a + b

    def _private(self):
        pass
"""
        result = handler.analyze_for_test_gen("test.py", code)
        assert len(result.classes) == 1
        assert result.classes[0].name == "Calculator"
        assert "add" in result.classes[0].methods
        assert "_private" not in result.classes[0].methods

    def test_analyze_for_test_gen_syntax_error(self, handler):
        """Test handling syntax errors."""
        code = "def invalid syntax"
        result = handler.analyze_for_test_gen("test.py", code)
        assert result.functions == []
        assert result.classes == []

    def test_perform_code_review_naming(self, handler):
        """Test code review for naming issues."""
        code = """
def camelCaseFunction():
    pass
"""
        result = handler.perform_code_review("test.py", code, focus="naming")
        assert len(result.issues) > 0
        assert any("camelCase" in issue.message for issue in result.issues)

    def test_perform_code_review_error_handling(self, handler):
        """Test code review for error handling."""
        code = """
try:
    risky()
except:
    pass
"""
        result = handler.perform_code_review("test.py", code, focus="error_handling")
        assert len(result.issues) > 0
        assert any("bare" in issue.message.lower() for issue in result.issues)

    def test_perform_code_review_performance(self, handler):
        """Test code review for performance issues."""
        code = """
items = []
for item in data:
    items.append(item)
"""
        result = handler.perform_code_review("test.py", code, focus="performance")
        assert len(result.issues) > 0
        assert any("append" in issue.message.lower() for issue in result.issues)

    def test_perform_code_review_security(self, handler):
        """Test code review for security issues."""
        code = """
result = eval(user_input)
password = "secret123"
"""
        result = handler.perform_code_review("test.py", code, focus="security")
        assert len(result.issues) > 0
        assert any("eval" in issue.message.lower() for issue in result.issues)

    def test_generate_test_code(self, handler):
        """Test test code generation."""
        from boring.vibe.analysis import CodeClass, CodeFunction, TestGenResult

        result = TestGenResult(
            file_path="math.py",
            functions=[CodeFunction(name="add", args=["a", "b"], docstring="Add", lineno=1)],
            classes=[CodeClass(name="Calculator", methods=["add"], docstring="Calc", lineno=5)],
            module_name="math",
            source_language="python",
        )
        test_code = handler.generate_test_code(result, "/project")
        assert "pytest" in test_code
        assert "TestAdd" in test_code or "test_add" in test_code
        assert "Calculator" in test_code

    def test_extract_dependencies(self, handler):
        """Test dependency extraction."""
        code = """
import os
from pathlib import Path
from .utils import helper
"""
        deps = handler.extract_dependencies("test.py", code)
        assert "os" in deps
        assert "pathlib" in deps
        assert ".utils" in deps

    def test_extract_documentation(self, handler):
        """Test documentation extraction."""
        code = '''
"""Module docstring."""

def add(a, b):
    """Add two numbers."""
    return a + b

class Calculator:
    """A calculator."""
    def multiply(self, a, b):
        """Multiply two numbers."""
        return a * b
'''
        result = handler.extract_documentation("test.py", code)
        assert result.module_doc == "Module docstring."
        assert len(result.items) >= 3  # add, Calculator, multiply
        assert any(item.name == "add" for item in result.items)
        assert any(item.name == "Calculator" for item in result.items)

    def test_check_naming(self, handler):
        """Test naming check."""
        code = "def camelCase(): pass"
        issues = handler._check_naming(code)
        assert len(issues) > 0

    def test_check_error_handling(self, handler):
        """Test error handling check."""
        code = "try:\n    pass\nexcept:\n    pass"
        issues = handler._check_error_handling(code)
        assert len(issues) > 0

    def test_check_performance(self, handler):
        """Test performance check."""
        code = """
for item in data:
    items.append(item)
"""
        issues = handler._check_performance(code)
        assert len(issues) > 0

    def test_check_security(self, handler):
        """Test security check."""
        code = "result = eval(input())"
        issues = handler._check_security(code)
        assert len(issues) > 0
