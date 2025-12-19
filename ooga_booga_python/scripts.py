
import subprocess
import sys

def lint():
    """Runs ruff check on the current directory."""
    print("Running ruff...")
    result = subprocess.run(["ruff", "check", "."])
    sys.exit(result.returncode)
