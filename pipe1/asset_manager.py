from pathlib import Path
import psycopg2

class Asset_Manager:
    def __init__(self, db_host="localhost", db_name="FX3X", user="postgres", password="Ifmatoodlon@321"):
        self.db_host = db_host
        self.db_name = db_name
        self.user = user
        self.password = password
        self._ensure_tables()

    def _connect(self):
        return psycopg2.connect(
            host=self.db_host,
            database=self.db_name,
            user=self.user,
            password=self.password
        )

    def _ensure_tables(self):
        """Create tables for assets, sequences, and shots if they don't exist, with UNIQUE constraints"""
        conn = self._connect()
        cur = conn.cursor()

        # Assets table: unique per project
        cur.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT,
            project_id INT REFERENCES projects(id),
            path TEXT,
            UNIQUE(name, project_id)
        );
        """)

        # Sequences table: unique per project
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sequences (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            project_id INT REFERENCES projects(id),
            path TEXT,
            UNIQUE(name, project_id)
        );
        """)

        # Shots table: unique per sequence
        cur.execute("""
        CREATE TABLE IF NOT EXISTS shots (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            sequence_id INT REFERENCES sequences(id),
            path TEXT,
            UNIQUE(name, sequence_id)
        );
        """)

        conn.commit()
        cur.close()
        conn.close()

    def create_asset(self, project_id, project_path, asset_name=None, asset_type=None):
        if not asset_name or not asset_type:
            raise ValueError("Asset name and type required")
        
        project_root = Path(project_path)
        asset_root = project_root / "assets" / asset_type / asset_name

        # create folder structure
        for dep in ["mod", "ldev", "anim", "fx", "lgt", "cfx"]:
            (asset_root / dep / "maya" / "scenes").mkdir(parents=True, exist_ok=True)
            (asset_root / dep / "houdini" / "scenes").mkdir(parents=True, exist_ok=True)

        asset_path = asset_root.as_posix()

        # write to database
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO assets (name, type, project_id, path)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (name, project_id) DO NOTHING;
        """, (asset_name, asset_type, project_id, asset_path))
        conn.commit()
        cur.close()
        conn.close()

        return asset_path

    def create_sequence(self, project_id, project_path, seq_name):
        if not seq_name:
            raise ValueError("Sequence name required")
        
        project_root = Path(project_path)
        seq_root = project_root / "seq" / seq_name
        seq_root.mkdir(parents=True, exist_ok=True)

        seq_path = seq_root.as_posix()

        conn = self._connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO sequences (name, project_id, path)
            VALUES (%s, %s, %s)
            ON CONFLICT (name, project_id) DO NOTHING;
        """, (seq_name, project_id, seq_path))
        conn.commit()
        cur.close()
        conn.close()

        return seq_path

    def create_shot(self, sequence_id, sequence_path, shot_name):
        if not shot_name:
            raise ValueError("Shot name required")

        shot_root = Path(sequence_path) / shot_name
        for dep in ["mod", "ldev", "anim", "fx", "lgt", "cfx"]:
            (shot_root / dep / "maya" / "scenes").mkdir(parents=True, exist_ok=True)
            (shot_root / dep / "houdini" / "scenes").mkdir(parents=True, exist_ok=True)

        shot_path = shot_root.as_posix()

        conn = self._connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO shots (name, sequence_id, path)
            VALUES (%s, %s, %s)
            ON CONFLICT (name, sequence_id) DO NOTHING;
        """, (shot_name, sequence_id, shot_path))
        conn.commit()
        cur.close()
        conn.close()

        return shot_path
