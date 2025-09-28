import os
from datetime import datetime
from pipe_common import ProjectInfo, AssetInfo, VersionInfo
from pipe_common.context import PipeContext  # our context reader
from pipe_common import env_vars

# --- Step 1: Simulate launching DCC and setting environment variables ---
# In your real desktop app, _build_environment() would fill these automatically.
os.environ[env_vars.PROJECT] = "Big Monster Movie"
os.environ[env_vars.SOFTWARE] = "houdini"
os.environ[env_vars.ASSET] = "ExplosionFX"
os.environ[env_vars.ASSET_TYPE] = "FX"
os.environ[env_vars.ARTIST_ID] = "101"
os.environ[env_vars.TASK_ID] = "555"
os.environ[env_vars.SHOT] = "sh010"
os.environ[env_vars.SEQUENCE] = "sq001"

# --- Step 2: Read context inside DCC ---
ctx = PipeContext.from_env()

print("Context read from environment variables:")
print(ctx)

# --- Step 3: Create a project (normally you’d insert into DB here) ---
project = ProjectInfo(
    id=None,
    name=ctx.project,  # from env
    description="A VFX-heavy show about a giant monster.",
    start_date=datetime(2024, 1, 1),
    status="active"
)
print("\nCreated Project:")
print(project)

# --- Step 4: Create an asset under this project ---
asset = AssetInfo(
    id=None,
    project_id=project.id,          # would be filled after DB insert
    asset_type_id=None,             # you’d map ctx.asset_type to an ID
    name=ctx.asset,                 # from env
    description=f"{ctx.asset} asset for project {ctx.project}",
    status="wip",
    version="v001",
    created_at=datetime.now(),
    updated_at=datetime.now(),
    artist_ids=[ctx.artist_id] if ctx.artist_id else None
)
print("\nCreated Asset:")
print(asset)

# --- Step 5: Simulate publishing a version ---
published_file_path = f"/mnt/projects/{ctx.project}/assets/{ctx.asset}/v001/{ctx.asset}_v001.usd"
version = VersionInfo(
    id=None,
    asset_id=None,                  # would be filled after DB insert of asset
    version_number="v001",
    file_path=published_file_path,
    thumbnail=f"/mnt/projects/{ctx.project}/assets/{ctx.asset}/preview.jpg",
    status="published",
    artist_id=ctx.artist_id,
    created_at=datetime.now()
)
print("\nPublished Version:")
print(version)
