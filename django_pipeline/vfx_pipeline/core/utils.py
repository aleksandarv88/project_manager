import os
from django.conf import settings

def create_asset_structure(base_path, asset_type, asset_name):
    """Create the base folder structure for a new asset."""
    asset_root = os.path.join(base_path, asset_type, asset_name)
    os.makedirs(asset_root, exist_ok=True)

    for dept in settings.ASSET_DEPARTMENTS:
        dept_root = os.path.join(asset_root, dept)
        os.makedirs(dept_root, exist_ok=True)
        if dept == "layout":
            os.makedirs(os.path.join(dept_root, "3DEqualizer"), exist_ok=True)

    return asset_root


def create_shot_structure(base_path, shot_name):
    """Create the base folder structure for a new shot."""
    shot_root = os.path.join(base_path, shot_name)
    os.makedirs(shot_root, exist_ok=True)

    for dept in settings.ASSET_DEPARTMENTS:
        dept_root = os.path.join(shot_root, dept)
        os.makedirs(dept_root, exist_ok=True)
        if dept == "layout":
            os.makedirs(os.path.join(dept_root, "3DEqualizer"), exist_ok=True)

    return shot_root
