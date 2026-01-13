import json
import os
import time
from importlib.metadata import version as get_version
from pathlib import Path

# Streamlit placeholder for test patching and lazy loading
st = None

from boring.paths import get_boring_path, get_state_file

# Paths
PROJECT_ROOT = Path.cwd()
STATUS_FILE = Path("status.json")
LOG_FILE = Path("logs/boring.log")
BRAIN_DIR = get_boring_path(PROJECT_ROOT, "brain", create=False)
CIRCUIT_FILE = get_state_file(PROJECT_ROOT, "circuit_breaker_state")
GLOBAL_BRAIN_FILE = Path.home() / ".boring" / "brain" / "global_patterns.json"


def load_global_brain_patterns() -> list:
    """Load patterns from global ~/.boring/brain/global_patterns.json (MCP Brain)."""
    if GLOBAL_BRAIN_FILE.exists():
        try:
            data = json.loads(GLOBAL_BRAIN_FILE.read_text(encoding="utf-8"))
            patterns = data.get("patterns", [])
            # Normalize to list of dicts for pandas
            result = []
            for p in patterns:
                result.append(
                    {
                        "pattern_id": p.get("id", p.get("pattern_id", "unknown")),
                        "pattern_type": p.get("type", p.get("pattern_type", "mcp_brain")),
                        "description": p.get("description", ""),
                        "context": p.get("error", p.get("context", "")),
                        "solution": p.get("fix", p.get("solution", "")),
                        "success_count": p.get("success_count", 1),
                        "last_used": p.get("timestamp", p.get("last_used", "")),
                        "source": "global_brain",
                    }
                )
            return result
        except Exception:
            return []
    return []


def load_json(path: Path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
    return None


def main():
    global st
    from boring.core.dependencies import DependencyManager

    if st is None:
        if not DependencyManager.check_gui():
            print("\n[bold red]Error: Dashboard requirements not found.[/bold red]")
            print("Please install the GUI optional dependencies:")
            print('  [bold]pip install "boring-aicoding[gui]"[/bold]\n')
            return

        import streamlit as st

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
        col1.metric("Loop Count", 0)
        col2.metric("Status", "READY", help="Run 'boring start' to begin autonomous development")
        col3.metric("API Calls (1h)", 0)

    if circuit_data:
        state = circuit_data.get("state", "CLOSED")
        failures = circuit_data.get("failures", 0)
        icon = "✅" if state == "CLOSED" else "🛑"
        col4.metric(
            "Circuit Breaker", f"{icon} {state}", f"{failures} Failures", delta_color="inverse"
        )
    else:
        col4.metric("Circuit Breaker", "✅ CLOSED", help="Circuit breaker is ready")

    # --- Welcome Banner (when no activity) ---
    if not status_data:
        st.info(
            """👋 **Welcome to Boring Dashboard!**

This dashboard monitors autonomous development loops. To see data:


1. **Run a loop**: `boring start` in your project directory
2. **Or use MCP tools**: The `boring_status` tool provides status via MCP

Below you can explore the Brain Map (learned patterns) and system configuration.
            """
        )

    st.markdown("---")

    # --- Data Loading ---
    from boring.services.storage import create_storage

    storage = create_storage(PROJECT_ROOT)

    # --- Main Layout ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📊 Live Logs", "📈 Usage Stats", "🧠 Brain Map", "🧬 Patterns", "⚙️ System Info"]
    )

    with tab2:
        st.subheader("Personal Usage Analytics")
        try:
             # Lazy import
            from boring.intelligence.usage_tracker import get_tracker
            tracker = get_tracker()
            stats = tracker.stats

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Tool Calls", stats.total_calls)
            c2.metric("Distinct Tools Used", len(stats.tools))
            if stats.last_updated:
                from datetime import datetime
                c3.metric("Last Activity", datetime.fromtimestamp(stats.last_updated).strftime("%H:%M:%S"))

            st.divider()

            # Prepare data for charts
            if stats.tools:
                import pandas as pd
                data = []
                for tname, usage in stats.tools.items():
                    data.append({"Tool": tname, "Calls": usage.count, "Last Used": usage.last_used})

                df_usage = pd.DataFrame(data).sort_values("Calls", ascending=False)

                # Chart
                st.bar_chart(df_usage, x="Tool", y="Calls")

                # Table
                st.dataframe(df_usage, use_container_width=True)
            else:
                st.info("No usage data recorded yet.")

        except Exception as e:
            st.error(f"Could not load usage stats: {e}")

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
            st.info(
                """📝 **No logs yet**

Logs will appear here once you run `boring start`.

**Quick Tips:**
- Create a `PROMPT.md` file with your task description
- Run `boring start` to begin the autonomous loop
- Logs will stream here in real-time
                """
            )

    with tab2:
        st.subheader("Brain Map (Visual Knowledge)")

        # Load patterns from BOTH local storage AND global MCP brain
        local_patterns = storage.get_patterns(limit=500)
        global_patterns = load_global_brain_patterns()
        # Mark local patterns with source
        for p in local_patterns:
            if "source" not in p:
                p["source"] = "local_project"
        # Merge patterns (global + local)
        all_patterns = global_patterns + local_patterns

        if all_patterns:
            import pandas as pd
            import streamlit.components.v1 as components

            df = pd.DataFrame(all_patterns)
            if "success_count" not in df.columns:
                df["success_count"] = 1
            if "pattern_type" not in df.columns:
                df["pattern_type"] = "unknown"

            # Metrics with source breakdown
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Patterns", len(all_patterns))
            c2.metric("Total Successes", df["success_count"].sum())
            c3.metric("From MCP Brain", len(global_patterns), help="Patterns from ~/.boring/brain/")
            c4.metric("From Local Project", len(local_patterns), help="Patterns from .boring/")

            st.divider()

            # --- Network Graph ---
            st.markdown("#### Knowledge Graph")

            # Prepare Nodes & Edges
            nodes = []
            edges = []
            types = df["pattern_type"].unique()

            # Central Brain Node
            nodes.append({"id": 0, "label": "BRAIN", "group": "brain", "value": 20})

            # Type Nodes
            type_map = {}
            for i, t in enumerate(types):
                tid = i + 1
                type_map[t] = tid
                nodes.append({"id": tid, "label": t.upper(), "group": "type", "value": 10})
                edges.append({"from": 0, "to": tid})

            # Pattern Nodes
            p_base_id = len(types) + 1
            for i, row in df.iterrows():
                pid = p_base_id + i
                val = max(5, min(20, row["success_count"] * 2))
                label = (
                    row["pattern_id"][:15] + "..."
                    if len(row["pattern_id"]) > 15
                    else row["pattern_id"]
                )

                nodes.append(
                    {
                        "id": pid,
                        "label": label,
                        "group": "pattern",
                        "title": f"ID: {row['pattern_id']}\nSuccess: {row['success_count']}",
                        "value": val,
                    }
                )
                # Edge to Type
                tid = type_map.get(row["pattern_type"], 0)
                edges.append({"from": tid, "to": pid})

            # Vis.js HTML Generation
            html = f"""
            <!DOCTYPE HTML>
            <html>
            <head>
              <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
              <style type="text/css">
                #mynetwork {{
                  width: 100%;
                  height: 600px;
                  background-color: #0e1117;
                  border: 1px solid #333;
                  border-radius: 8px;
                }}
              </style>
            </head>
            <body>
            <div id="mynetwork"></div>
            <script type="text/javascript">
              var nodes = new vis.DataSet({json.dumps(nodes)});
              var edges = new vis.DataSet({json.dumps(edges)});
              var container = document.getElementById('mynetwork');
              var data = {{ nodes: nodes, edges: edges }};
              var options = {{
                nodes: {{
                  shape: 'dot',
                  font: {{ size: 14, color: '#ffffff' }},
                  borderWidth: 2
                }},
                groups: {{
                  brain: {{ color: '#ff4b4b', size: 30 }},
                  type: {{ color: '#00ccff', size: 20 }},
                  pattern: {{ color: '#00ff99' }}
                }},
                edges: {{
                  width: 1,
                  color: {{ color: '#555555', highlight: '#00ccff' }},
                  smooth: {{ type: 'continuous' }}
                }},
                physics: {{
                  stabilization: false,
                  barnesHut: {{ gravitationalConstant: -2000, springConstant: 0.04 }}
                }},
                interaction: {{ hover: true }}
              }};
              var network = new vis.Network(container, data, options);
            </script>
            </body>
            </html>
            """
            components.html(html, height=620)

            # Interactive Explorer (Table)
            st.markdown("#### Recent Operations")
            st.dataframe(
                df[["pattern_id", "pattern_type", "success_count", "last_used"]].sort_values(
                    "last_used", ascending=False
                ),
                use_container_width=True,
            )
        else:
            st.info(
                """🧠 **Brain is empty - Ready to auto-learn!**

The Brain **automatically learns** error→solution patterns as you work. No manual action needed!


**Auto-Learning triggers:**
- ✨ **MCP tools**: `boring_code_review`, `boring_vibe_check`, `boring_suggest_next` etc.
- ✨ **Autonomous loops**: `boring start` captures patterns during development
- ✨ **Error fixes**: When AI fixes an error, the pattern is auto-saved

**Storage locations:**
- `~/.boring/brain/` - Global MCP Brain (cross-project)
- `.boring/` - Local project patterns

Just start using Boring tools - the Brain will populate automatically! 🚀
                """
            )

    with tab3:
        st.subheader("Pattern Explorer (Database)")

        search = st.text_input("Search Patterns", placeholder="e.g. auth error")
        if search:
            results = storage.get_patterns(context_like=search, limit=20)
        else:
            results = storage.get_patterns(limit=20)

        for p in results:
            with st.expander(f"{p.get('pattern_type')} - {p.get('pattern_id')}"):
                st.markdown(f"**Description:** {p.get('description')}")
                st.markdown(f"**Context:**\n```\n{p.get('context')}\n```")
                st.markdown(f"**Solution:**\n```\n{p.get('solution')}\n```")
                st.caption(f"Successes: {p.get('success_count')} | Last Used: {p.get('last_used')}")

    with tab4:
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
    from boring.core.dependencies import DependencyManager

    # Check dependencies
    if not DependencyManager.check_gui():
        print("\n[bold red]Error: Streamlit is required for the web dashboard.[/bold red]")
        print('Please install it with: [bold]pip install "boring-aicoding[gui]"[/bold]\n')
        return

    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(script_path)] + sys.argv[1:])
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
