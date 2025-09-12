from pathlib import Path

class AssetManager:
    DEPARTMENTS = ["mod", "ldev", "anim", "fx", "lgt", "cfx", "layout", "env"]
    ASSET_TYPES = ["props", "env", "vehicle", "fx"]

    # Template for department folder structure
    DEPARTMENT_TEMPLATE = {
        "software": {
            "usd": {
                "data": {}
            }
        }
    }

    # Full nested structure for assets and shots
    @staticmethod
    def get_full_dep_structure():
        return {
            "software": {
                "usd": {
                    "data": {},  # software_name_v###.ext goes here
                }
            }
        }

    def __init__(self, show_path: str):
        self.show_path = Path(show_path)
        if not self.show_path.exists():
            raise ValueError(f"Show path does not exist: {self.show_path}")

    def create_asset(self, asset_type: str, asset_name: str):
        """Create asset folder with full structure under given asset type."""
        if asset_type not in self.ASSET_TYPES:
            raise ValueError(f"Unknown asset type: {asset_type}")

        asset_root = self.show_path / "assets" / asset_type / asset_name
        asset_root.mkdir(parents=True, exist_ok=True)

        for dep in self.DEPARTMENTS:
            dep_root = asset_root / dep
            self._create_dep_structure(dep_root)

        return asset_root

    def _create_dep_structure(self, base_path: Path):
        """Recursive creation of department structure for asset or shot."""
        def recursive_create(base: Path, struct: dict):
            for name, subtree in struct.items():
                target = base / name
                target.mkdir(exist_ok=True)
                if isinstance(subtree, dict) and subtree:
                    recursive_create(target, subtree)

        # Clone full department structure
        recursive_create(base_path, self.get_full_dep_structure())
