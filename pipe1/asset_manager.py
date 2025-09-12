import os
import shutil
import psycopg2

class Asset_Manager:
    def __init__(self, db_connect_func):
        self._connect_db = db_connect_func

    def create_asset(self, project_id, project_path, asset_name, asset_type):
        asset_path = os.path.join(project_path, "assets", asset_type, asset_name)
        os.makedirs(asset_path, exist_ok=True)
        try:
            conn = self._connect_db()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO assets (project_id, name, type, path) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING;",
                (project_id, asset_name, asset_type, asset_path)
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            raise RuntimeError(f"Failed to insert asset into DB: {e}")
        return asset_path

    def create_sequence(self, project_id, project_path, seq_name):
        seq_path = os.path.join(project_path, "sequences", seq_name)
        os.makedirs(seq_path, exist_ok=True)
        try:
            conn = self._connect_db()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO sequences (project_id, name, path) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;",
                (project_id, seq_name, seq_path)
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            raise RuntimeError(f"Failed to insert sequence into DB: {e}")
        return seq_path

    def create_shot(self, seq_id, seq_path, shot_name):
        shot_path = os.path.join(seq_path, shot_name)
        os.makedirs(shot_path, exist_ok=True)
        try:
            conn = self._connect_db()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO shots (sequence_id, name, path) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;",
                (seq_id, shot_name, shot_path)
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            raise RuntimeError(f"Failed to insert shot into DB: {e}")
        return shot_path

    def delete_item(self, path):
        if os.path.exists(path):
            shutil.rmtree(path)
        else:
            raise FileNotFoundError(f"Path does not exist: {path}")
