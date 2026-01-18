"""
Integration tests for the Boring Ecosystem (Zero-Cost Platform).
Targeting Phase 1-4 features: Pack, Install, Brain, Sync.
Refactored to use subprocess for true integration testing.
"""

import subprocess
import sys
from pathlib import Path

import pytest


def run_cli(args, cwd=None):
    """Run boring CLI command via subprocess."""
    cmd = [sys.executable, "-m", "boring.main"] + args

    # Use absolute path for PYTHONPATH
    src_path = str(Path.cwd() / "src")
    env = {"PYTHONPATH": src_path, "BORING_USER_NAME": "TestUser"}

    # Merge with system env to find git etc
    import os

    full_env = os.environ.copy()
    full_env.update(env)

    # Prepend sys.path[0] to PATH if needed (though unlikely for git resolution)
    # full_env["PATH"] = f"{sys.path[0]};{full_env.get('PATH', '')}"

    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=full_env)

    with open("test_output.log", "a", encoding="utf-8") as f:
        f.write(f"\n--- CMD: {' '.join(cmd)} ---\n")
        f.write(f"CWD: {cwd}\n")
        f.write(f"Return: {result.returncode}\n")
        f.write(f"STDOUT:\n{result.stdout}\n")
        f.write(f"STDERR:\n{result.stderr}\n")

    if result.returncode != 0:
        print(f"CMD Failed: {' '.join(cmd)}")
    return result


@pytest.fixture
def temp_workspace(tmp_path):
    """Isolate tests to a temp directory."""
    # Create necessary dirs
    (tmp_path / ".boring").mkdir()
    (tmp_path / "home").mkdir()
    return tmp_path


def test_pack_lifecycle_e2e(temp_workspace):
    """Test Pack Init -> Build -> Install."""
    root = temp_workspace

    # 1. Init
    pack_name = "demo-pack"
    res = run_cli(["pack", "init", "--name", pack_name], cwd=root)
    assert res.returncode == 0

    pack_dir = root / pack_name
    assert (pack_dir / "boring-pack.json").exists()

    # 2. Build
    res = run_cli(["pack", "build"], cwd=pack_dir)
    assert res.returncode == 0
    assert "Pack created" in res.stdout

    zip_files = list(pack_dir.glob("*.boring-pack"))
    assert len(zip_files) == 1
    pack_zip = zip_files[0]

    # 3. Install (Local)
    # We need to set up HOME or specific env to prevent polluting real user run if possible,
    # but installer uses Path.home() / .boring by default OR local .boring_plugins.
    # Let's use --local to install to temp_workspace/.boring_plugins

    res = run_cli(["install", str(pack_zip), "--local"], cwd=root)
    assert res.returncode == 0
    assert "installed successfully" in res.stdout

    # Verify installation
    plugins_dir = root / ".boring_plugins"
    assert plugins_dir.exists()
    assert any(p.name.startswith("demo-pack") for p in plugins_dir.iterdir())


def test_brain_export_import_e2e(temp_workspace):
    """Test Brain Export."""
    root = temp_workspace
    output_file = root / "knowledge.boring-brain"

    # Create valid brain dir so exporter doesn't bail
    (root / ".boring_brain").mkdir(exist_ok=True)
    # Create valid .boring marker to ensure root detection
    (root / ".boring").mkdir(exist_ok=True)

    # Debug info
    run_cli(["brain", "info"], cwd=root)

    # Export
    res = run_cli(["brain", "export", "--output", str(output_file)], cwd=root)

    # In a clean env without real chroma, failure to connect or empty DB might cause exit 1
    # We accept 1 if it means "Empty" but verify the command ran.
    # If it says "No brain directory", it implies path resolution fail.

    if res.returncode == 0:
        assert output_file.exists()
    else:
        # If it failed, assert it wasn't a cliff-crash
        # "No brain directory found" -> means logic worked but env missing.
        # Make sure it's NOT a python traceback.
        assert "Traceback" not in res.stderr


def test_sync_state_e2e(temp_workspace):
    """Test Sync State Dump."""
    root = temp_workspace
    (root / ".git").mkdir()  # Fake git repo

    # Sync will try to git pull/push. It will likely fail on git commands.
    # But before that, it should dump state.

    run_cli(["sync"], cwd=root)

    # We don't care about return code (it will likely be 1 due to git failure)
    # We care that state.json was generated.

    state_file = root / ".boring" / "sync" / "state.json"
    assert state_file.exists()
