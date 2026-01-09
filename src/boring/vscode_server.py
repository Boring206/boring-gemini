"""
VS Code Integration Server (V10.15)

JSON-RPC server for VS Code extension integration.
Exposes Boring functionality via WebSocket/HTTP for IDE integration.
"""

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from .config import settings
from .logger import get_logger

logger = get_logger("vscode_server")


@dataclass
class RPCRequest:
    """JSON-RPC 2.0 Request."""

    jsonrpc: str
    method: str
    params: dict[str, Any]
    id: Optional[int] = None


@dataclass
class RPCResponse:
    """JSON-RPC 2.0 Response."""

    jsonrpc: str = "2.0"
    result: Any = None
    error: Optional[dict] = None
    id: Optional[int] = None

    def to_dict(self) -> dict:
        d = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error:
            d["error"] = self.error
        else:
            d["result"] = self.result
        return d


class VSCodeServer:
    """
    V10.15: JSON-RPC Server for VS Code Integration.

    Provides:
    - boring.verify: Run verification on a file/project
    - boring.evaluate: Evaluate code quality
    - boring.search: RAG search
    - boring.status: Get project status
    - boring.fix: Auto-fix issues

    Usage:
        server = VSCodeServer()
        await server.start(port=9876)
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or settings.PROJECT_ROOT
        self._handlers: dict[str, Callable] = {}
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register RPC method handlers."""
        self._handlers = {
            "boring.verify": self._handle_verify,
            "boring.evaluate": self._handle_evaluate,
            "boring.search": self._handle_search,
            "boring.status": self._handle_status,
            "boring.fix": self._handle_fix,
            "boring.version": self._handle_version,
        }

    async def handle_request(self, data: str) -> str:
        """Handle incoming JSON-RPC request."""
        try:
            raw = json.loads(data)
            req = RPCRequest(
                jsonrpc=raw.get("jsonrpc", "2.0"),
                method=raw.get("method", ""),
                params=raw.get("params", {}),
                id=raw.get("id"),
            )

            handler = self._handlers.get(req.method)
            if not handler:
                return json.dumps(
                    RPCResponse(
                        error={"code": -32601, "message": f"Method not found: {req.method}"},
                        id=req.id,
                    ).to_dict()
                )

            result = await handler(req.params)
            return json.dumps(RPCResponse(result=result, id=req.id).to_dict())

        except json.JSONDecodeError:
            return json.dumps(
                RPCResponse(error={"code": -32700, "message": "Parse error"}, id=None).to_dict()
            )
        except Exception as e:
            return json.dumps(
                RPCResponse(
                    error={"code": -32603, "message": str(e)},
                    id=raw.get("id") if "raw" in dir() else None,
                ).to_dict()
            )

    async def _handle_verify(self, params: dict) -> dict:
        """Handle verify request."""
        from .verification import CodeVerifier

        level = params.get("level", "STANDARD")
        filepath = params.get("file")

        verifier = CodeVerifier(self.project_root)

        if filepath:
            result = verifier.verify_file(Path(filepath), level)
            return {"passed": result.passed, "message": result.message, "details": result.details}
        else:
            passed, msg = verifier.verify_project(level)
            return {"passed": passed, "message": msg}

    async def _handle_evaluate(self, params: dict) -> dict:
        """Handle evaluate request."""
        filepath = params.get("file")
        if not filepath:
            return {"error": "file parameter required"}

        path = Path(filepath)
        if not path.exists():
            return {"error": f"File not found: {filepath}"}

        try:
            from .judge import LLMJudge, create_judge_provider

            provider = create_judge_provider()
            judge = LLMJudge(provider)

            content = path.read_text(encoding="utf-8", errors="replace")
            result = judge.grade_code(path.name, content)
            return result
        except Exception as e:
            return {"error": str(e)}

    async def _handle_search(self, params: dict) -> dict:
        """Handle RAG search request."""
        query = params.get("query", "")
        if not query:
            return {"error": "query parameter required"}

        try:
            from .rag.rag_retriever import RAGRetriever

            retriever = RAGRetriever(self.project_root)

            if not retriever.is_available:
                return {"error": "RAG not available. Run 'boring rag index' first."}

            results = retriever.retrieve(query, top_k=params.get("limit", 5))
            return {
                "results": [
                    {
                        "file": r.file_path,
                        "name": r.name,
                        "score": r.score,
                        "snippet": r.content[:200],
                    }
                    for r in results
                ]
            }
        except Exception as e:
            return {"error": str(e)}

    async def _handle_status(self, params: dict) -> dict:
        """Handle status request."""
        try:
            from .intelligence import MemoryManager

            memory = MemoryManager(self.project_root)
            state = memory.get_project_state()
            return state
        except Exception as e:
            return {"error": str(e)}

    async def _handle_fix(self, params: dict) -> dict:
        """Handle auto-fix request."""
        filepath = params.get("file")
        if not filepath:
            return {"error": "file parameter required"}

        # Return command template (actual fix runs via CLI)
        return {
            "command": f"boring auto-fix {filepath}",
            "status": "PENDING",
            "message": "Run the command to execute auto-fix",
        }

    async def _handle_version(self, params: dict) -> dict:
        """Handle version request."""
        try:
            from importlib.metadata import version

            ver = version("boring")
        except Exception:
            ver = "10.15.0"
        return {"version": ver, "project": str(self.project_root)}

    async def start(self, host: str = "127.0.0.1", port: int = 9876) -> None:
        """Start the JSON-RPC server."""

        def _silence_windows_socket_errors(loop, context):
            """Silence benign WinError 10054/10053 in asyncio Proactor loop."""
            exception = context.get("exception")
            if isinstance(
                exception, (ConnectionResetError, ConnectionAbortedError, BrokenPipeError)
            ):
                return  # Ignore these noisy errors on Windows disconnects
            loop.default_exception_handler(context)

        loop = asyncio.get_running_loop()
        loop.set_exception_handler(_silence_windows_socket_errors)

        async def handle_client(reader, writer):
            addr = writer.get_extra_info("peername")
            logger.info(f"Connection from {addr}")

            try:
                while True:
                    data = await reader.readline()
                    if not data:
                        break

                    response = await self.handle_request(data.decode())
                    writer.write((response + "\n").encode())
                    await writer.drain()
            except (ConnectionResetError, BrokenPipeError):
                logger.info(f"Client {addr} disconnected abruptly")
            except Exception as e:
                logger.error(f"Client error: {e}")
            finally:
                try:
                    writer.close()
                    await writer.wait_closed()
                except (ConnectionResetError, BrokenPipeError):
                    pass  # Already closed by remote

        server = await asyncio.start_server(handle_client, host, port)
        logger.info(f"VS Code server started on {host}:{port}")

        async with server:
            await server.serve_forever()


def run_vscode_server(port: int = 9876):
    """Entry point for VS Code server."""
    server = VSCodeServer()
    asyncio.run(server.start(port=port))
