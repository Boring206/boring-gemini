
import sys
import os

# Add the project's 'src' directory to sys.path
project_root = r"D:\User\Desktop\ralphgeminicode\boring-gemini"
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

print("Attempting to import boring.mcp.server...")
# Now import and run the server
try:
    from boring.mcp.server import run_server
    print("Successfully imported boring.mcp.server.")
    print("Calling run_server()...")
    run_server()
    print("run_server() finished (this should ideally not happen if server is running indefinitely).")
except ImportError as e:
    print(f"Failed to import boring.mcp.server: {e}")
    sys.exit(1)
except Exception as e:
    print(f"An error occurred during server execution: {e}")
    sys.exit(1)

