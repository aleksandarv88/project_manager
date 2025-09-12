from pathlib import Path
import psycopg2

class Project_Manager:
    def __init__(self, db_name="FX3X", user="postgres", password="Ifmatoodlon@321", host="localhost"):
        self.db_name = db_name
        self.user = user
        self.password = password
        self.host = host
        self._ensure_db()
        self._ensure_table()

    def _ensure_db(self):
        conn = psycopg2.connect(host=self.host, database="postgres",
                                user=self.user, password=self.password)
        cur = conn.cursor()
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname='{self.db_name}'")
        if not cur.fetchone():
            cur.execute(f"CREATE DATABASE {self.db_name}")
            print(f"Database {self.db_name} created!")
        cur.close()
        conn.commit()
        conn.close()

    def _ensure_table(self):
        conn = psycopg2.connect(host=self.host, database=self.db_name,
                                user=self.user, password=self.password)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE,
                path TEXT
            )
        """)
        conn.commit()
        cur.close()
        conn.close()

    def create_project(self, show_name, show_path):
        # Create folder structure with pathlib
        project_root = Path(show_path) / show_name
        assets_path = project_root / "assets"
        seq_path = project_root / "seq"

        assets_path.mkdir(parents=True, exist_ok=True)
        seq_path.mkdir(parents=True, exist_ok=True)
        print(f"Project folders created at {project_root}")

        # Normalize path to forward slashes for DB
        project_root_str = project_root.as_posix()

        # Insert into database
        conn = psycopg2.connect(host=self.host, database=self.db_name,
                                user=self.user, password=self.password)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO projects (name, path) VALUES (%s, %s) ON CONFLICT (name) DO NOTHING",
            (show_name, project_root_str)
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"Project '{show_name}' added to database.")
