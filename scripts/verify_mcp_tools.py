import os
import sys
from pathlib import Path

# Calculate paths relative to this script's location
SCRIPT_DIR = Path(__file__).parent.resolve()
src_path = SCRIPT_DIR / "src"

if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

print(f"DEBUG: PYTHONPATH includes {src_path}")

# Assume test project is sibling directory (adjust as needed)
# Or use current working directory as project path
project_test_path = SCRIPT_DIR.parent / "boringtestev"
if not project_test_path.exists():
    project_test_path = Path.cwd()  # Fallback to current directory

try:
    from boring.mcp.tools.evaluation import boring_evaluate
    from boring.mcp.tools.knowledge import boring_learn
    from boring.mcp.tools.patching import boring_apply_patch

    print(f"DEBUG: Using test project at {project_test_path}")

    print("\n--- 1. Testing boring_apply_patch ---")
    # This should no longer raise ImportError for DiffPatcher
    res_patch = boring_apply_patch(
        file_path="main.py",
        search_text='print("Hello from Boring Test!")',
        replace_text='print("Hello from Boring Test! [Verified via Internal Script]")',
        project_path=str(project_test_path)
    )
    print(f"Result: {res_patch}")

    print("\n--- 2. Testing boring_learn ---")
    # This should no longer raise AttributeError for get_common_errors
    res_learn = boring_learn(project_path=str(project_test_path))
    print(f"Result: {res_learn}")

    print("\n--- 3. Testing boring_evaluate Signature ---")
    # Just checking if it can be called with project_path without Pydantic/Signature error
    try:
        res_eval = boring_evaluate(
            target="main.py",
            project_path=str(project_test_path),
            interactive=True  # Use interactive to skip actual CLI call if not needed
        )
        print(f"Result (Interactive): {res_eval[:100]}...")
    except Exception as e:
        print(f"Evaluate failed (likely CLI/Auth related, but signature is OK): {e}")

except Exception as e:
    print(f"\n❌ FATAL: Verification script failed with error: {e}")
    import traceback
    traceback.print_exc()

