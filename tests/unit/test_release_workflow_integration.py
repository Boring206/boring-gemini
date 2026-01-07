
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import shutil
import boring.setup

def test_setup_copies_release_workflow(tmp_path):
    """Verify that setup_new_project copies the release-prep workflow."""
    
    project_name = "test_project_release_wf"
    project_path = tmp_path / project_name
    
    # We must ensure we don't accidentally run git commands in the real repo
    # So we mock subprocess.run to be safe.
    # BUT we want 'mkdir' and file writing to be real.
    
    with patch("subprocess.run") as mock_run:
        # Mock git init/add/commit to succeed
        mock_run.return_value = MagicMock(returncode=0)
        
        # Determine strict CWD behavior
        original_cwd = os.getcwd()
        try:
            # Change to tmp_path so setup_new_project creates project there
            os.chdir(tmp_path)
            
            # Call setup
            boring.setup.setup_new_project(project_name)
            
        finally:
            os.chdir(original_cwd)

    # Check if workflow file exists
    workflow_file = project_path / ".agent" / "workflows" / "release-prep.md"
    
    # Debug info
    print(f"DEBUG: Checking {workflow_file}")
    if not workflow_file.exists():
        print("DEBUG: File content of project:")
        for p in project_path.rglob("*"):
             print(f"  {p}")

    assert workflow_file.exists(), f"release-prep.md should be copied to .agent/workflows"
    
    content = workflow_file.read_text(encoding="utf-8")
    assert "Release Preparation Checklist" in content
