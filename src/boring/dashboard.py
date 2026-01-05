import json
import os
import time
from importlib.metadata import version as get_version
from pathlib import Path

# Streamlit placeholder for test patching and lazy loading
st = None

# Paths


# Paths

# Paths
STATUS_FILE = Path("status.json")
LOG_FILE = Path("logs/boring.log")
BRAIN_DIR = Path(".boring_brain")
CIRCUIT_FILE = Path(".circuit_breaker_state")


def load_json(path: Path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
    return None


def main():
    global st
    if st is None:
        try:
            import streamlit as streamlit_mod
            st = streamlit_mod
        except ImportError:
            # Use a safe way to show help if streamlit is missing
            print("\n[bold red]Error: Dashboard requirements not found.[/bold red]")
            print("Please install the GUI optional dependencies:")
            print('  [bold]pip install "boring[gui]"[/bold]\n')
            return

    # Configuration (Must be first streamlit call)
    st.set_page_config(
        page_title="Boring Dashboard",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🤖 Boring Monitor")
    st.markdown("### Autonomous Agent Dashboard")

    # --- Sidebar ---
    st.sidebar.header("Controls")
    refresh_rate = st.sidebar.slider("Refresh Rate (s)", 1, 10, 2)

    if st.sidebar.button("Refresh Now"):
        st.rerun()

    st.sidebar.markdown("---")
    try:
        boring_version = get_version("boring-gemini")
    except Exception:
        boring_version = "7.2.0"
    st.sidebar.markdown(f"**Version**: {boring_version}")
    st.sidebar.markdown("**Backend**: Local CLI")

    # --- Top Metrics (Status) ---
    status_data = load_json(STATUS_FILE)
    circuit_data = load_json(CIRCUIT_FILE)

    col1, col2, col3, col4 = st.columns(4)

    if status_data:
        loop_count = status_data.get("loop_count", 0)
        status = status_data.get("status", "Unknown")
        calls = status_data.get("calls_made_this_hour", 0)

        col1.metric("Loop Count", loop_count)
        col2.metric(
            "Status", status.upper(), delta_color="normal" if status == "running" else "off"
        )
        col3.metric("API Calls (1h)", calls)
    else:
        col1.metric("Loop Count", "N/A")
        col2.metric("Status", "OFFLINE")

    if circuit_data:
        state = circuit_data.get("state", "CLOSED")
        failures = circuit_data.get("failures", 0)
        icon = "✅" if state == "CLOSED" else "🛑"
        col4.metric(
            "Circuit Breaker", f"{icon} {state}", f"{failures} Failures", delta_color="inverse"
        )
    else:
        col4.metric("Circuit Breaker", "Unknown")

    st.markdown("---")

    # --- Main Layout ---
    tab1, tab2, tab3 = st.tabs(["📊 Live Logs", "🧠 Brain Explorer", "⚙️ System Info"])

    with tab1:
        st.subheader("Live Logs")
        if LOG_FILE.exists():
            # Read last 50 lines for performance
            try:
                with open(LOG_FILE, encoding="utf-8") as f:
                    lines = f.readlines()[-100:]

                log_text = "".join(lines)
                st.code(log_text, language="text")
            except Exception as e:
                st.error(f"Error reading logs: {e}")
        else:
            st.warning("No log file found.")

    with tab2:
        st.subheader("Knowledge Base (.boring_brain)")

        if BRAIN_DIR.exists():
            # List structure
            col_tree, col_content = st.columns([1, 2])

            with col_tree:
                st.markdown("#### Structure")
                for root, _dirs, files in os.walk(BRAIN_DIR):
                    level = root.replace(str(BRAIN_DIR), "").count(os.sep)
                    indent = "&nbsp;" * 4 * level
                    st.markdown(f"{indent}📁 **{os.path.basename(root)}/**", unsafe_allow_html=True)
                    subindent = "&nbsp;" * 4 * (level + 1)
                    for f in files:
                        st.markdown(f"{subindent}📄 {f}", unsafe_allow_html=True)

            with col_content:
                st.markdown("#### File Viewer")
                # Simple file selector
                all_files = []
                for root, _, files in os.walk(BRAIN_DIR):
                    for file in files:
                        if file.endswith(".md") or file.endswith(".json"):
                            all_files.append(Path(root) / file)

                selected_file = st.selectbox(
                    "Select file to view", all_files, format_func=lambda x: x.name
                )

                if selected_file:
                    content = selected_file.read_text(encoding="utf-8")
                    if selected_file.suffix == ".json":
                        st.json(json.loads(content))
                    else:
                        st.markdown(content)
        else:
            st.info("Brain directory not initialized yet.")

    with tab3:
        st.subheader("System Configuration")
        st.json(
            {
                "Project Root": os.getcwd(),
                "Streamlit Version": st.__version__,
                "Log File": str(LOG_FILE.absolute()),
                "Status File": str(STATUS_FILE.absolute()),
            }
        )

    # Auto-refresh using session_state (non-blocking pattern)
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = time.time()

    if refresh_rate > 0:
        elapsed = time.time() - st.session_state.last_refresh
        if elapsed >= refresh_rate:
            st.session_state.last_refresh = time.time()
            st.rerun()


def run_app():
    """Entry point for the boring-dashboard CLI command."""
    import subprocess
    import sys
    from pathlib import Path

    # Find this script's path
    script_path = Path(__file__).resolve()

    # Run streamlit
    import importlib.util

    if importlib.util.find_spec("streamlit") is None:
        print("\n[bold red]Error: Streamlit is required for the web dashboard.[/bold red]")
        print('Please install it with: [bold]pip install "boring[gui]"[/bold]\n')
        return

    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(script_path)] + sys.argv[1:])
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
