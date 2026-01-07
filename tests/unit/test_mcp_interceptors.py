"""
Unit tests for boring.mcp.interceptors module.
"""

from unittest.mock import MagicMock, patch

from boring.mcp import interceptors


class TestInterceptors:
    """Tests for stdout interceptors."""

    def test_bytes_interceptor_write_passthrough(self):
        """Test BytesInterceptor with passthrough enabled."""
        mock_buffer = MagicMock()
        mock_parent = MagicMock()
        mock_parent._passthrough = True

        interceptor = interceptors._BytesInterceptor(mock_buffer, mock_parent)

        interceptor.write(b"test data")

        mock_buffer.write.assert_called_once_with(b"test data")

    def test_bytes_interceptor_write_mcp_started(self):
        """Test BytesInterceptor when MCP has started."""
        mock_buffer = MagicMock()
        mock_parent = MagicMock()
        mock_parent._passthrough = False
        mock_parent._mcp_started = True

        interceptor = interceptors._BytesInterceptor(mock_buffer, mock_parent)

        interceptor.write(b"test data")

        mock_buffer.write.assert_called_once()

    def test_bytes_interceptor_write_jsonrpc(self):
        """Test BytesInterceptor with JSON-RPC message."""
        mock_buffer = MagicMock()
        mock_parent = MagicMock()
        mock_parent._passthrough = False
        mock_parent._mcp_started = False

        interceptor = interceptors._BytesInterceptor(mock_buffer, mock_parent)

        jsonrpc_data = b'{"jsonrpc": "2.0", "method": "test"}'
        interceptor.write(jsonrpc_data)

        mock_buffer.write.assert_called_once()
        assert mock_parent._mcp_started is True

    def test_bytes_interceptor_write_newline(self):
        """Test BytesInterceptor with newline."""
        mock_buffer = MagicMock()
        mock_parent = MagicMock()
        mock_parent._passthrough = False
        mock_parent._mcp_started = False

        interceptor = interceptors._BytesInterceptor(mock_buffer, mock_parent)

        interceptor.write(b"\n")

        mock_buffer.write.assert_called_once_with(b"\n")

    def test_bytes_interceptor_write_memoryview(self):
        """Test BytesInterceptor with memoryview."""
        mock_buffer = MagicMock()
        mock_parent = MagicMock()
        mock_parent._passthrough = False
        mock_parent._mcp_started = False

        interceptor = interceptors._BytesInterceptor(mock_buffer, mock_parent)

        with patch("os.environ.get", return_value="1"), patch("sys.stderr.write"):
            data = memoryview(b"test")
            result = interceptor.write(data)

            assert result == len(data)

    def test_stdout_interceptor_write_passthrough(self):
        """Test StdoutInterceptor with passthrough enabled."""
        mock_stdout = MagicMock()

        with patch("os.environ.get", return_value="1"):
            interceptor = interceptors._StdoutInterceptor(mock_stdout)

            interceptor.write("test data")

            mock_stdout.write.assert_called_once_with("test data")

    def test_stdout_interceptor_write_mcp_started(self):
        """Test StdoutInterceptor when MCP has started."""
        mock_stdout = MagicMock()

        with patch("os.environ.get", return_value="0"):
            interceptor = interceptors._StdoutInterceptor(mock_stdout)
            interceptor._mcp_started = True

            interceptor.write("test data")

            mock_stdout.write.assert_called_once()

    def test_stdout_interceptor_write_jsonrpc(self):
        """Test StdoutInterceptor with JSON-RPC message."""
        mock_stdout = MagicMock()

        with patch("os.environ.get", return_value="0"):
            interceptor = interceptors._StdoutInterceptor(mock_stdout)

            jsonrpc_data = '{"jsonrpc": "2.0", "method": "test"}'
            interceptor.write(jsonrpc_data)

            mock_stdout.write.assert_called_once()
            assert interceptor._mcp_started is True

    def test_stdout_interceptor_write_newline(self):
        """Test StdoutInterceptor with newline."""
        mock_stdout = MagicMock()

        with patch("os.environ.get", return_value="0"):
            interceptor = interceptors._StdoutInterceptor(mock_stdout)

            interceptor.write("\n")

            mock_stdout.write.assert_called_once_with("\n")

    def test_stdout_interceptor_write_empty(self):
        """Test StdoutInterceptor with empty data."""
        mock_stdout = MagicMock()

        with patch("os.environ.get", return_value="0"):
            interceptor = interceptors._StdoutInterceptor(mock_stdout)

            interceptor.write("")

            # Should return early, no write
            mock_stdout.write.assert_not_called()

    def test_stdout_interceptor_flush(self):
        """Test StdoutInterceptor flush."""
        mock_stdout = MagicMock()

        interceptor = interceptors._StdoutInterceptor(mock_stdout)
        interceptor.flush()

        mock_stdout.flush.assert_called_once()

    def test_stdout_interceptor_getattr(self):
        """Test StdoutInterceptor __getattr__."""
        mock_stdout = MagicMock()
        mock_stdout.some_attribute = "value"

        interceptor = interceptors._StdoutInterceptor(mock_stdout)

        assert interceptor.some_attribute == "value"
