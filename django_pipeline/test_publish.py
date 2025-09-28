import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from pipe_common import ProjectInfo, AssetInfo, VersionInfo

# --- 1. Connect to testdb ---
conn = psycopg2.connect(
    host="localhost",
    dbname="testdb",
    user="postgres",
    password="yourpassword"
)
conn.autocommit = True  # easier for this demo

# --- 2. Create tables if not exist ---
with conn.cursor() as cur:
    # Projects table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id SERIAL PRIMARY KEY,
        name TEXT,
        description TEXT,
        start_date DATE,
        status TEXT
    )
    """)
    # Assets table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        id SERIAL PRIMARY KEY,
        project_id INT REFERENCES projects(id),
        asset_type_id INT,
        name TEXT,
        description TEXT,
        status TEXT,
        version TEXT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    """)
    # Versions table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS versions (
        id SERIAL PRIMARY KEY,
        asset_id INT REFERENCES assets(id),
        version_number TEXT,
        file_path TEXT,
        thumbnail TEXT,
        status TEXT,
        artist_id INT,
        created_at TIMESTAMP
    )
    """)

# --- 3. Insert a project ---
project = ProjectInfo(
    id=None,
    name="Big Monster Movie",
    description="A VFX-heavy show about a giant monster.",
    start_date=datetime(2024, 1, 1),
    status="active"
)

with conn.cursor(cursor_factory=RealDictCursor) as cur:
    cur.execute("""
        INSERT INTO projects (name, description, start_date, status)
        VALUES (%s, %s, %s, %s)
        RETURNING *
    """, (project.name, project.description, project.start_date, project.status))
    project_row = cur.fetchone()
    project.id = project_row["id"]

print("Created Project:")
print(project)

# --- 4. Insert an asset under this project ---
asset = AssetInfo(
    id=None,
    project_id=project.id,
    asset_type_id=2,
    name="ExplosionFX",
    description="Large hero explosion asset",
    status="wip",
    version="v001",
    created_at=datetime.now(),
    updated_at=datetime.now(),
    artist_ids=[101, 102]  # not stored in this simple demo
)

with conn.cursor(cursor_factory=RealDictCursor) as cur:
    cur.execute("""
        INSERT INTO assets (project_id, asset_type_id, name, description, status, version, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
    """, (asset.project_id, asset.asset_type_id, asset.name, asset.description,
          asset.status, asset.version, asset.created_at, asset.updated_at))
    asset_row = cur.fetchone()
    asset.id = asset_row["id"]

print("\nCreated Asset:")
print(asset)

# --- 5. Publish a version ---
published_file_path = "/mnt/projects/bigshow/assets/ExplosionFX/v001/ExplosionFX_v001.usd"

version = VersionInfo(
    id=None,
    asset_id=asset.id,
    version_number="v001",
    file_path=published_file_path,
    thumbnail="/mnt/projects/bigshow/assets/ExplosionFX/preview.jpg",
    status="published",
    artist_id=101,
    created_at=datetime.now()
)

with conn.cursor(cursor_factory=RealDictCursor) as cur:
    cur.execute("""
        INSERT INTO versions (asset_id, version_number, file_path, thumbnail, status, artist_id, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING *
    """, (version.asset_id, version.version_number, version.file_path,
          version.thumbnail, version.status, version.artist_id, version.created_at))
    version_row = cur.fetchone()
    version.id = version_row["id"]

print("\nPublished Version:")
print(version)

# --- 6. Fetch back all assets with their versions ---
with conn.cursor(cursor_factory=RealDictCursor) as cur:
    cur.execute("""
        SELECT a.id as asset_id, a.name as asset_name, v.version_number, v.file_path
        FROM assets a
        LEFT JOIN versions v ON a.id = v.asset_id
        WHERE a.project_id = %s
    """, (project.id,))
    rows = cur.fetchall()
    print("\nAssets and Versions in Project:")
    for row in rows:
        print(row)

conn.close()
