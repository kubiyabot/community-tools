from pathlib import Path

def get_script_files():
    """Get all script files from the scripts directory."""
    scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
    script_files = {}
    for script_path in scripts_dir.glob("*.py"):
        with open(script_path, "r") as f:
            script_files[script_path.name] = f.read()
    return script_files 