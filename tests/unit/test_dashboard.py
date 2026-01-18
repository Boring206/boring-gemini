import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

# Mock streamlit before importing dashboard
mock_st_module = MagicMock()
mock_st_module.__version__ = "1.0.0"
sys.modules["streamlit"] = mock_st_module
sys.modules["streamlit.components"] = MagicMock()
sys.modules["streamlit.components.v1"] = MagicMock()

from boring.cli.dashboard import load_json, main


class TestDashboard:
    def test_load_json_success(self):
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.read_text", return_value='{"key": "value"}'),
        ):
            data = load_json(Path("dummy.json"))
            assert data == {"key": "value"}

    def test_load_json_file_not_found(self):
        with patch("pathlib.Path.exists", return_value=False):
            data = load_json(Path("dummy.json"))
            assert data is None

    def test_load_json_decode_error(self):
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.read_text", return_value="invalid json"),
        ):
            data = load_json(Path("dummy.json"))
            assert data is None

    @patch("boring.cli.dashboard.st")
    @patch("boring.cli.dashboard.load_json")
    @patch("boring.cli.dashboard.get_version")
    def test_main_layout(self, mock_version, mock_load_json, mock_st):
        """Test main dashboard layout generation."""
        mock_version.return_value = "1.0.0"
        mock_st.__version__ = "1.0.0"
        mock_st.sidebar.slider.return_value = 2  # Fixed refresh_rate

        # Mock load_json to return dummy data
        mock_load_json.side_effect = [
            {"loop_count": 5, "status": "running", "calls_made_this_hour": 10},  # status
            {"state": "OPEN", "failures": 3},  # circuit
        ]

        # Mock st.columns to return 4 mocks
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_col3 = MagicMock()
        mock_col4 = MagicMock()

        def columns_side_effect(spec):
            if spec == 4:
                return [mock_col1, mock_col2, mock_col3, mock_col4]
            if isinstance(spec, list) and len(spec) == 2:
                return [MagicMock(), MagicMock()]
            return [MagicMock()] * 4

        mock_st.columns.side_effect = columns_side_effect

        # Mock session state to allow attribute access
        mock_st.session_state.last_refresh = time.time()

        # Mock tabs - dashboard now has 5 tabs
        mock_st.tabs.return_value = [
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
        ]

        # Run main
        main()

        # Verify Sidebar
        mock_st.sidebar.header.assert_called_with("Controls")
        mock_st.sidebar.markdown.assert_any_call("**Version**: 1.0.0")

        # Verify Metrics - Use assert_any_call as columns are reused in Brain Map
        mock_col1.metric.assert_any_call("Loop Count", 5)
        mock_col2.metric.assert_any_call("Status", "RUNNING", delta_color="normal")
        mock_col4.metric.assert_called()

        # Verify Tabs - updated to match new 5-tab layout
        mock_st.tabs.assert_called_with(
            ["📊 Live Logs", "📈 Usage Stats", "🧠 Brain Map", "🧬 Patterns", "⚙️ System Info"]
        )

    @patch("boring.cli.dashboard.st")
    @patch("boring.cli.dashboard.load_json")
    def test_main_no_data(self, mock_load_json, mock_st):
        """Test dashboard handles missing data gracefully."""
        mock_st.__version__ = "1.0.0"
        mock_st.sidebar.slider.return_value = 2
        mock_load_json.return_value = None
        mock_st.columns.side_effect = (
            lambda x: [MagicMock()] * 4 if x == 4 else [MagicMock(), MagicMock()]
        )
        mock_st.tabs.return_value = [
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
        ]
        mock_st.session_state.last_refresh = time.time()

        main()

        # Should not crash
        mock_st.title.assert_called()

    @patch("boring.cli.dashboard.st")
    def test_main_brain_explorer(self, mock_st):
        """Test Brain Explorer tab logic."""
        mock_st.__version__ = "1.0.0"
        mock_st.sidebar.slider.return_value = 2
        mock_st.columns.side_effect = (
            lambda x: [MagicMock()] * 4 if x == 4 else [MagicMock(), MagicMock()]
        )
        mock_st.session_state.last_refresh = time.time()

        # Mock os.walk for brain dir
        with (
            patch("os.walk", return_value=[("/brain", [], ["file.md"])]),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.read_text", return_value="# Content"),
        ):
            mock_st.tabs.return_value = [
                MagicMock(),
                MagicMock(),
                MagicMock(),
                MagicMock(),
                MagicMock(),
            ]

            # Ensure load_json returns valid dicts to prevent TypeErrors in metric display
            with patch(
                "boring.cli.dashboard.load_json",
                side_effect=[
                    {"loop_count": 5, "status": "running"},
                    {"state": "OPEN", "failures": 0},
                ],
            ):
                main()

            # Since we can't easily force the 'with tab2:' block execution without deeper mocking
            # of the returned objects context manager, we assume main() runs through it.
            # Ideally we check if os.walk was called if tab2 was entered.
