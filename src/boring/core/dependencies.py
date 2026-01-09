"""
Dependency Manager for Boring V4.0

Centralizes logic for checking and requiring optional dependencies.
This ensures consistent error messages and avoids eager imports of heavy libraries.
"""

from typing import Optional


class DependencyManager:
    """Manages optional dependencies for the Boring framework."""

    _chroma_available: Optional[bool] = None
    _gui_available: Optional[bool] = None
    _mcp_available: Optional[bool] = None

    @classmethod
    def check_chroma(cls) -> bool:
        """Check if Vector DB dependencies (ChromaDB + Sentence Transformers) are installed."""
        if cls._chroma_available is None:
            try:
                import chromadb  # noqa: F401
                import sentence_transformers  # noqa: F401

                cls._chroma_available = True
            except ImportError:
                cls._chroma_available = False
        return cls._chroma_available

    @classmethod
    def require_chroma(cls) -> None:
        """Raise ImportError if Vector DB dependencies are missing."""
        if not cls.check_chroma():
            raise ImportError(
                "Vector database features require extra dependencies.\n"
                'Please install with: [bold]pip install "boring-aicoding[vector]"[/bold]'
            )

    @classmethod
    def check_gui(cls) -> bool:
        """Check if GUI dependencies (Streamlit) are installed."""
        if cls._gui_available is None:
            try:
                import streamlit  # noqa: F401

                cls._gui_available = True
            except ImportError:
                cls._gui_available = False
        return cls._gui_available

    @classmethod
    def require_gui(cls) -> None:
        """Raise ImportError if GUI dependencies are missing."""
        if not cls.check_gui():
            raise ImportError(
                "The dashboard requires extra dependencies.\n"
                'Please install with: [bold]pip install "boring-aicoding[gui]"[/bold]'
            )

    @classmethod
    def check_mcp(cls) -> bool:
        """Check if MCP server dependencies are installed."""
        if cls._mcp_available is None:
            try:
                import fastmcp  # noqa: F401

                cls._mcp_available = True
            except ImportError:
                cls._mcp_available = False
        return cls._mcp_available

    @classmethod
    def require_mcp(cls) -> None:
        """Raise ImportError if MCP dependencies are missing."""
        if not cls.check_mcp():
            raise ImportError(
                "MCP server requires extra dependencies.\n"
                'Please install with: [bold]pip install "boring-aicoding[mcp]"[/bold]'
            )
