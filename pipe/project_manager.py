import os

# Departments and software examples
DEPARTMENTS = ["mod", "ldev", "anim", "fx", "lgt", "cfx"]
SOFTWARES = ["maya", "houdini"]
ASSET_TYPES = ["props", "env", "vehicle", "fx"]

class Project_Manager:
    def __init__(self):
        pass

    def create_folder_structure(self, show_path, show_name):
        """
        Create the full PIPELINE_FOLDER_STRUCTURE at the given path.
        """
        root = os.path.join(show_path, show_name)
        os.makedirs(root, exist_ok=True)

        # ASSETS
        assets_root = os.path.join(root, "assets")
        os.makedirs(assets_root, exist_ok=True)

        for asset_type in ASSET_TYPES:
            asset_type_path = os.path.join(assets_root, asset_type)
            os.makedirs(asset_type_path, exist_ok=True)

            # placeholder asset_name example, can be empty initially
            asset_name_path = os.path.join(asset_type_path, "asset_name")
            os.makedirs(asset_name_path, exist_ok=True)

            # Add departments for each asset
            for dep in DEPARTMENTS:
                dep_path = os.path.join(asset_name_path, dep)
                os.makedirs(dep_path, exist_ok=True)

                for software in SOFTWARES:
                    software_path = os.path.join(dep_path, software)
                    os.makedirs(software_path, exist_ok=True)

                    scenes_artist_path = os.path.join(software_path, "scenes", "artist_name")
                    os.makedirs(scenes_artist_path, exist_ok=True)

                    # Scenes folder and USD folder
                    usd_path = os.path.join(scenes_artist_path, "usd")
                    data_path = os.path.join(usd_path, "data")
                    os.makedirs(data_path, exist_ok=True)

        # SEQUENCES
        seq_root = os.path.join(root, "seq")
        os.makedirs(seq_root, exist_ok=True)
        # placeholder sequence and shot example
        seq_name_path = os.path.join(seq_root, "seq_name")
        os.makedirs(seq_name_path, exist_ok=True)

        shot_name_path = os.path.join(seq_name_path, "shot_name")
        os.makedirs(shot_name_path, exist_ok=True)

        for dep in DEPARTMENTS:
            dep_path = os.path.join(shot_name_path, dep)
            os.makedirs(dep_path, exist_ok=True)

            for software in SOFTWARES:
                software_path = os.path.join(dep_path, software)
                os.makedirs(software_path, exist_ok=True)

                scenes_artist_path = os.path.join(software_path, "scenes", "artist_name")
                os.makedirs(scenes_artist_path, exist_ok=True)

                usd_path = os.path.join(scenes_artist_path, "usd")
                data_path = os.path.join(usd_path, "data")
                os.makedirs(data_path, exist_ok=True)

        # Shot publish folder
        publish_path = os.path.join(shot_name_path, "publish", "usd")
        os.makedirs(publish_path, exist_ok=True)

        for dep in DEPARTMENTS:
            dep_publish_path = os.path.join(publish_path, dep)
            os.makedirs(dep_publish_path, exist_ok=True)

        # Sequence publish folder
        seq_publish_path = os.path.join(seq_name_path, "publish", "usd")
        os.makedirs(seq_publish_path, exist_ok=True)

        for dep in DEPARTMENTS:
            dep_seq_publish_path = os.path.join(seq_publish_path, dep)
            os.makedirs(dep_seq_publish_path, exist_ok=True)

        print(f"Folder structure for '{show_name}' created at {show_path}")
