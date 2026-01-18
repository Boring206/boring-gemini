
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd() / "src"))

from boring.cli.wizard import WizardManager

def diagnostic():
    print("--- Boring Wizard Path Diagnostic ---")
    manager = WizardManager()
    
    print(f"System: {manager.system}")
    print(f"Home: {manager.home}")
    print(f"AppData: {manager.appdata}")
    print(f"LocalAppData: {manager.localappdata}")
    
    print("\n[Scanning Editors...]")
    found = manager.scan_editors()
    for name, path in found.items():
        # Handle dummy paths
        is_dummy = name in ["Gemini CLI", "Codex CLI", "Neovim", "Qwen Code", "Cline"]
        exists = "EXISTS" if (is_dummy or path.exists() or path.parent.exists()) else "MISSING"
        print(f"Editor: {name}")
        print(f"Path  : {path}")
        print(f"Status: {exists}")
        print("-" * 20)
        
    print("\n[Scanning MCP Ecosystem...]")
    ecosystem = manager.scan_ecosystem()
    if ecosystem:
        print(f"  Found: {', '.join(ecosystem)}")
    else:
        print("  No external MCP servers detected in standard paths.")
    
    print("\n--- Diagnostic Complete ---")

if __name__ == "__main__":
    diagnostic()
