from pathlib import Path

def create_recursive(base: Path, struct: dict):
    """Recursively create folders from nested dict structure."""
    for name, subtree in struct.items():
        target = base / name
        target.mkdir(parents=True, exist_ok=True)
        if isinstance(subtree, dict) and subtree:
            create_recursive(target, subtree)
