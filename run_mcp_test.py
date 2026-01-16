
import subprocess
import sys
import os

python_executable = r"C:\Python312\python.exe"
module_name = "boring.mcp.server"

# Set PYTHONPATH to the project root for this subprocess call
project_root = r"D:\User\Desktop\ralphgeminicode\boring-gemini"
env = os.environ.copy()
env["PYTHONPATH"] = project_root

command = [python_executable, "-m", module_name]

print(f"Attempting to run command: {' '.join(command)}")
print(f"With PYTHONPATH: {env['PYTHONPATH']}")

try:
    result = subprocess.run(command, env=env, capture_output=True, text=True, check=True)
    print("STDOUT:")
    print(result.stdout)
    print("STDERR:")
    print(result.stderr)
except subprocess.CalledProcessError as e:
    print(f"Command failed with exit code {e.returncode}")
    print("STDOUT:")
    print(e.stdout)
    print("STDERR:")
    print(e.stderr)
except FileNotFoundError:
    print(f"Error: Python executable not found at {python_executable}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
