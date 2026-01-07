# ==============================================================================
# CRITICAL: STDOUT INTERCEPTOR FOR MCP DEBUGGING
# This MUST be at the very top, BEFORE any other imports
# It captures any write to stdout and logs the stack trace to stderr
# ==============================================================================
import os
import sys


class _BytesInterceptor:
    """
    Intercepts binary writes to stdout.buffer.
    This is necessary because some libraries (like Rich) may write directly to buffer
    or use binary mode, bypassing the text-based _StdoutInterceptor.
    """

    def __init__(self, original_buffer, parent):
        self._original = original_buffer
        self._parent = parent

    def write(self, data):
        # Handle both bytes and memoryview
        if isinstance(data, memoryview):
            data_bytes = data.tobytes()
        else:
            data_bytes = data

        if self._parent._passthrough or self._parent._mcp_started:
            return self._original.write(data)

        # AUTO-ALLOW JSON-RPC messages
        stripped = data_bytes.strip()
        if stripped.startswith(b"{") and b'"jsonrpc"' in data_bytes:
            self._parent._mcp_started = True
            return self._original.write(data)

        if data_bytes in (b"\n", b"\r\n", b"\r"):
            return self._original.write(data)

        # If BORING_MCP_MODE is not set, let it through
        if os.environ.get("BORING_MCP_MODE") != "1":
            return self._original.write(data)

        # Log to stderr
        try:
            # Attempt to decode for cleaner logs, fallback to repr
            try:
                text = data_bytes.decode("utf-8", errors="replace")
                sys.stderr.write(f"\n[STDOUT POLLUTION (BYTES)] {text[:200]}\n")
            except:
                sys.stderr.write(f"\n[STDOUT POLLUTION (BYTES)] {repr(data_bytes[:200])}\n")
        except:
            pass

        # Return length to pretend we wrote it
        return len(data)

    def flush(self):
        self._original.flush()

    def __getattr__(self, name):
        return getattr(self._original, name)


class _StdoutInterceptor:
    """
    Intercepts all writes to stdout and logs them to stderr with stack trace.
    This helps identify which module/code is polluting the stdout stream.

    In production MCP mode, this prevents any non-JSON output from reaching stdout.
    The interceptor can be disabled by setting BORING_MCP_DEBUG_PASSTHROUGH=1.
    """

    def __init__(self, original_stdout):
        self._original = original_stdout
        self._passthrough = os.environ.get("BORING_MCP_DEBUG_PASSTHROUGH") == "1"
        self._mcp_started = False
        self._buffer_wrapper = None

    def write(self, data: str):
        if not data:
            return

        # If passthrough is enabled or MCP has started, let it through
        if self._passthrough or self._mcp_started:
            return self._original.write(data)

        # AUTO-ALLOW JSON-RPC messages
        # We check for '{' which starts a JSON-RPC object.
        # We avoid '[' because it often captures log messages starting with '[INFO]'.
        # For maximum reliability, we also check for the "jsonrpc" key.
        stripped = data.strip()
        if stripped.startswith("{") and '"jsonrpc"' in data:
            self._mcp_started = True
            return self._original.write(data)

        # Also allow newlines that follow JSON (buffered writes)
        if data in ("\n", "\r\n", "\r"):
            return self._original.write(data)

        # Otherwise, log the pollution attempt to stderr
        # If BORING_MCP_MODE is not set, we might be in testing/CLI mode, so let it through if not MCP started
        if os.environ.get("BORING_MCP_MODE") != "1":
            return self._original.write(data)

        sys.stderr.write(f"\n[STDOUT POLLUTION] {repr(data[:200])}\n")
        return

    def flush(self):
        self._original.flush()

    def fileno(self):
        return self._original.fileno()

    def isatty(self):
        # FORCE FALSE to prevent tools like Rich from auto-detecting TTY and
        # using using buffer/colors which might bypass interception
        return False

    def mark_mcp_started(self):
        """Call this when MCP protocol handshake begins to allow JSON-RPC through."""
        self._mcp_started = True

    @property
    def encoding(self):
        return self._original.encoding

    @property
    def errors(self):
        return getattr(self._original, "errors", None)

    @property
    def buffer(self):
        """Return the intercepted binary buffer."""
        if self._buffer_wrapper is None:
            # Check if original has buffer (it should)
            if hasattr(self._original, "buffer"):
                self._buffer_wrapper = _BytesInterceptor(self._original.buffer, self)
            else:
                return None
        return self._buffer_wrapper

    @property
    def mode(self):
        return getattr(self._original, "mode", "w")

    @property
    def name(self):
        return getattr(self._original, "name", "<stdout>")

    @property
    def newlines(self):
        return getattr(self._original, "newlines", None)

    @property
    def line_buffering(self):
        return getattr(self._original, "line_buffering", False)

    @property
    def write_through(self):
        return getattr(self._original, "write_through", False)

    def readable(self):
        return False

    def writable(self):
        return True

    def seekable(self):
        return False

    def close(self):
        pass  # Don't close stdout

    def detach(self):
        return self._original.detach()

    def __getattr__(self, name):
        return getattr(self._original, name)


def install_interceptors():
    """Install the stdout interceptor."""
    if not isinstance(sys.stdout, _StdoutInterceptor):
        sys.stdout = _StdoutInterceptor(sys.stdout)
