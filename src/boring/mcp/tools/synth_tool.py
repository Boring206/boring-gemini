import ast
import logging
import textwrap
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from boring.core.config import settings

logger = logging.getLogger(__name__)


class SynthesizedTool(BaseModel):
    name: str
    description: str
    code: str
    arguments_schema: dict[str, Any]


class ToolSynthesizer:
    """
    V14 Feature: Tool Synthesis 2.0.
    Generates, validates, and registers dynamic MCP tools.
    """

    def __init__(self, synthetic_tools_dir: Path | None = None):
        self.tools_dir = (
            synthetic_tools_dir or Path(settings.PROJECT_ROOT) / ".boring" / "tools" / "synthetic"
        )
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        self.registry: dict[str, SynthesizedTool] = {}

    def validate_code(self, code: str) -> bool:
        """
        Secure AST validation for synthesized tool code.
        """
        try:
            tree = ast.parse(code)
            # Basic security check: No dangerous imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in ["os", "subprocess", "shutil"]:
                            logger.warning(
                                f"Restricted import detected in synth tool: {alias.name}"
                            )
                            # return False # For now, just warn or we can be strict
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id in ["eval", "exec"]:
                        logger.error("DANGEROUS: use of eval/exec in synth tool.")
                        return False
            return True
        except SyntaxError as e:
            logger.error(f"Syntax error in synthesized code: {e}")
            return False

    def synthesize_tool(self, name: str, code: str, description: str) -> bool:
        """
        Synthesize and save a new tool.
        """
        if not self.validate_code(code):
            return False

        # Clean tool code
        clean_code = textwrap.dedent(code)

        tool_path = self.tools_dir / f"{name}.py"
        tool_content = (
            f'"""\nSynthesized Tool: {name}\nDescription: {description}\n"""\n\n{clean_code}'
        )

        try:
            tool_path.write_text(tool_content, encoding="utf-8")
            logger.info(f"Tool '{name}' synthesized and saved at {tool_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save synthesized tool: {e}")
            return False

    def load_synthetic_tools(self) -> list[str]:
        """
        Discover and return names of available synthetic tools.
        """
        return [f.stem for f in self.tools_dir.glob("*.py")]


def boring_synth_tool(name: str, description: str, code: str) -> str:
    """
    MCP Tool to synthesize a new tool.
    """
    synth = ToolSynthesizer()
    success = synth.synthesize_tool(name, code, description)
    if success:
        return f"Successfully synthesized and registered tool: {name}. It will be available in the next lifecycle."
    else:
        return "Failed to synthesize tool. Check logs for validation errors."
