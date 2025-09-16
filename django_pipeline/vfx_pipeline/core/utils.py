# core/utils.py
import os
from django.conf import settings

def create_shot_structure(base_path, shot_name):
    shot_root = os.path.join(base_path, shot_name)

    for dept in settings.ASSET_DEPARTMENTS:
        for software in settings.ASSET_SOFTWARES:
            path = os.path.join(shot_root, dept, software, "scenes")
            os.makedirs(path, exist_ok=True)

            # 👇 extra folder for layout department
            if dept == "layout":
                eq_path = os.path.join(shot_root, dept, "3DEqualizer")
                os.makedirs(eq_path, exist_ok=True)

    return shot_root


