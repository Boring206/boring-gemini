
import json
from pathlib import Path
import sys

sys.path.append(str(Path.cwd() / "src"))
from boring.cli.wizard import WizardManager

def test_ecosystem_detection():
    print("--- Testing Ecosystem Detection ---")
    manager = WizardManager()
    
    # Create a dummy config file
    dummy_config = Path("dummy_mcp_config.json")
    config_data = {
        "mcpServers": {
            "critical-thinker": {
                "command": "npx",
                "args": ["-y", "@anthropics/mcp-criticalthink"]
            },
            "context7-docs": {
                "command": "npx",
                "args": ["-y", "@context7/mcp"]
            }
        }
    }
    dummy_config.write_text(json.dumps(config_data))
    
    try:
        # Mock the found_editors to include our dummy
        manager.found_editors = {"Mock Editor": dummy_config}
        discovered = manager.scan_ecosystem()
        
        print(f"Discovered: {discovered}")
        
        expected = ["criticalthink", "context7"] # normalized in scan_ecosystem text check
        # Wait, my scan_ecosystem is simple text check: if "context7" in text: discovered.add("context7")
        
        for e in ["criticalthink", "context7"]:
            if e in discovered:
                print(f"✅ Detected {e}")
            else:
                print(f"❌ Failed to detect {e}")
                
    finally:
        if dummy_config.exists():
            dummy_config.unlink()

if __name__ == "__main__":
    test_ecosystem_detection()
