from pathlib import Path
from typing import Dict, Any, Optional


# Template for what every department looks like
DEPARTMENT_TEMPLATE: Dict[str, Any] = {
    "software": {
        "artist_name": {
            "usd": {
                "data": {}
            }
        }
    }
}

# Departments that should each get the template
DEPARTMENTS = ["mod", "ldev", "anim", "fx", "lgt", "cfx", "layout", "env"]


# Helper function: expand all departments for reuse
def department_block() -> Dict[str, Any]:
    return {dep: DEPARTMENT_TEMPLATE for dep in DEPARTMENTS}


DEFAULT_STRUCTURE: Dict[str, Any] = {
    "assets": {
        "asset_type": {                      # placeholder (props/env/vehicle/fx)
            "asset_name": department_block()
        },
        "props": {
            "asset_name": department_block()
        },
        "env": {
            "asset_name": department_block()
        },
        "vehicle": {
            "asset_name": department_block()
        },
        "char": {
            "asset_name": department_block()
        },
    },
    "seq": {
        "seq_name": {
            "shot_name": {
                **department_block(),
                "publish": {
                    "usd": {
                        "dep_name": {}
                    }
                }
            },
            "publish": {
                "usd": {
                    "dep_name": {}
                }
            }
        }
    }
}


class ProjectStructure:
    """
    Create a show's folder tree on disk.
    """

    def __init__(self, show_name: str, root_location: str, structure: Optional[Dict[str, Any]] = None):
        self.show_name = show_name.strip()
        if not self.show_name:
            raise ValueError("show_name must not be empty")
        self.root = Path(root_location).expanduser().resolve() / self.show_name
        self.structure = structure if structure is not None else DEFAULT_STRUCTURE

    def _create_recursive(self, base: Path, struct: Dict[str, Any]):
        """Recursively create folders from nested dict structure."""
        for name, subtree in struct.items():
            target = base / name
            target.mkdir(parents=True, exist_ok=True)
            if isinstance(subtree, dict) and subtree:
                self._create_recursive(target, subtree)

    def create_show(self) -> Path:
        """Create the full show structure and return the show root Path."""
        self.root.mkdir(parents=True, exist_ok=True)
        self._create_recursive(self.root, self.structure)
        return self.root

if __name__ == "__main__":
    ps = ProjectStructure("MyShow", "D:/projects")
    created = ps.create_show()
    print("Created:", created)
