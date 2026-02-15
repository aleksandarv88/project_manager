"""
Generic asset publisher for DCC apps (Maya, Houdini, etc.).

Usage (generic Python):
    from pipeline_scripts.publish_asset import publish_asset
    asset = publish_asset(
        name="tree_oak_A",
        asset_type="prop",
        project_name="ForestShow",
        description="Hero oak tree",
        image_path=r"C:\\renders\\oak_thumb.jpg",  # optional
        extra={"department": "env"},                 # optional, stored in DB if field exists
    )
    print(asset)

CLI:
    python -m pipeline_scripts.publish_asset \
        --name tree_oak_A --type prop --project ForestShow \
        --description "Hero oak tree" --image C:\path\thumb.jpg

Environment:
    PIPELINE_DB_NAME, PIPELINE_DB_USER, PIPELINE_DB_PASSWORD, PIPELINE_DB_HOST, PIPELINE_DB_PORT

Notes:
    - Upserts Asset by (project_id, name).
    - Resolves project by name; creates project if missing (with minimal fields).
    - Image path is copied to project media folder only if accessible; otherwise stored as original path.
"""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

try:
    # Optional: use Django API if available
    from . import api_client  # type: ignore
except Exception:  # noqa: BLE001
    api_client = None


# ---------- Config ----------

DEFAULTS = {
    "dbname": os.environ.get("DB_NAME") or os.environ.get("PIPELINE_DB_NAME", "FX3X"),
    "user": os.environ.get("DB_USER") or os.environ.get("PIPELINE_DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD") or os.environ.get("PIPELINE_DB_PASSWORD", ""),
    "host": os.environ.get("DB_HOST") or os.environ.get("PIPELINE_DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT") or os.environ.get("PIPELINE_DB_PORT", "5432"),
}


@dataclass
class AssetRecord:
    id: int
    name: str
    asset_type: str
    project_id: int
    image: Optional[str]


def _connect() -> psycopg2.extensions.connection:
    conn = psycopg2.connect(**DEFAULTS)
    conn.autocommit = True
    return conn


def _fetchone(conn, query: str, params: tuple) -> Optional[Dict[str, Any]]:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params)
        row = cur.fetchone()
        return dict(row) if row else None


def _execute(conn, query: str, params: tuple) -> None:
    with conn.cursor() as cur:
        cur.execute(query, params)


def _default_base_path() -> str:
    for var in (
        "PIPELINE_PROJECT_BASE_PATH",
        "PIPELINE_PROJECTS_BASE",
        "PIPELINE_BASE_PATH",
    ):
        value = os.environ.get(var)
        if value:
            return value
    # Reasonable cross‑platform fallback
    if os.name == "nt":
        return r"D:\\"
    return "/projects"


def _ensure_project(conn, project_name: str) -> Dict[str, Any]:
    # Prefer API if configured
    if api_client and (os.environ.get("PIPELINE_API_BASE") or os.environ.get("API_BASE_URL")):
        resp = api_client.api_post("/api/projects/", {"name": project_name, "base_path": _default_base_path()})
        if not resp.get("ok"):
            raise RuntimeError(f"API error creating project: {resp}")
        data = resp.get("data", {})
        return {"id": data.get("id"), "name": data.get("name"), "base_path": data.get("base_path")}
    row = _fetchone(
        conn,
        "SELECT id, name, base_path FROM core_project WHERE name = %s",
        (project_name,),
    )
    if row:
        return row
    # Create a minimal project (ensure base_path is provided to satisfy NOT NULL)
    base_path = _default_base_path()
    _execute(
        conn,
        "INSERT INTO core_project (name, base_path) VALUES (%s, %s)",
        (project_name, base_path),
    )
    return _fetchone(
        conn,
        "SELECT id, name, base_path FROM core_project WHERE name = %s",
        (project_name,),
    ) or {"id": 0, "name": project_name, "base_path": None}


def _copy_image_to_project(image_path: Path, project: Dict[str, Any]) -> Optional[str]:
    if not image_path.exists():
        return None
    base = project.get("base_path")
    if not base:
        return str(image_path)
    target_dir = Path(base) / project.get("name", "project") / "media" / "assets"
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / image_path.name
        if str(image_path.resolve()) != str(target.resolve()):
            shutil.copy2(str(image_path), str(target))
        return str(target)
    except Exception:
        return str(image_path)


def publish_asset(
    *,
    name: str,
    asset_type: str,
    project_name: str,
    description: str = "",
    image_path: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> AssetRecord:
    """Create or update an Asset under the given project.

    Returns the resulting AssetRecord.
    """
    if not name or not asset_type or not project_name:
        raise ValueError("name, asset_type and project_name are required")

    # API mode
    if api_client and (os.environ.get("PIPELINE_API_BASE") or os.environ.get("API_BASE_URL")):
        project = _ensure_project(None, project_name)  # type: ignore[arg-type]
        project_id = int(project.get("id") or 0)
        resp = api_client.api_post(
            "/api/assets/",
            {"project_id": project_id, "name": name, "asset_type": asset_type},
        )
        if not resp.get("ok"):
            raise RuntimeError(f"API error creating asset: {resp}")
        data = resp.get("data", {})
        return AssetRecord(
            id=int(data.get("id", 0)),
            name=str(data.get("name", name)),
            asset_type=str(data.get("asset_type", asset_type)),
            project_id=int(data.get("project_id", project_id)),
            image=None,
        )

    conn = _connect()
    try:
        project = _ensure_project(conn, project_name)
        project_id = int(project["id"]) if project else 0

        # Upsert by (project_id, name)
        row = _fetchone(
            conn,
            "SELECT id, name, asset_type, project_id, image FROM core_asset WHERE project_id = %s AND name = %s",
            (project_id, name),
        )

        image_db_value: Optional[str] = None
        if image_path:
            image_db_value = _copy_image_to_project(Path(image_path), project)

        if row:
            # Update
            fields = ["asset_type = %s"]
            params: list[Any] = [asset_type]
            # description/image may not exist in model; update only if column exists
            if description:
                try:
                    _execute(conn, "UPDATE core_asset SET description = %s WHERE id = %s", (description, int(row["id"])) )
                except Exception:
                    pass
            if image_db_value:
                try:
                    _execute(conn, "UPDATE core_asset SET image = %s WHERE id = %s", (image_db_value, int(row["id"])) )
                except Exception:
                    pass
            _execute(
                conn,
                f"UPDATE core_asset SET {', '.join(fields)} WHERE project_id = %s AND name = %s",
                tuple(params + [project_id, name]),
            )
        else:
            cols = ["name", "asset_type", "project_id"]
            vals = [name, asset_type, project_id]
            # optional fields if supported
            if description:
                try:
                    cols.append("description")
                    vals.append(description)
                except Exception:
                    pass
            if image_db_value:
                cols.append("image")
                vals.append(image_db_value)
            placeholders = ", ".join(["%s"] * len(vals))
            _execute(
                conn,
                f"INSERT INTO core_asset ({', '.join(cols)}) VALUES ({placeholders})",
                tuple(vals),
            )

        final = _fetchone(
            conn,
            "SELECT id, name, asset_type, project_id, image FROM core_asset WHERE project_id = %s AND name = %s",
            (project_id, name),
        )
        if not final:
            raise RuntimeError("Failed to upsert asset")
        return AssetRecord(
            id=int(final["id"]),
            name=str(final["name"]),
            asset_type=str(final["asset_type"]),
            project_id=int(final["project_id"]),
            image=(str(final.get("image")) if final.get("image") else None),
        )
    finally:
        try:
            conn.close()
        except Exception:
            pass


# ---------- Minimal DCC shims ----------

def publish_from_env(default_asset_type: str = "prop") -> AssetRecord:
    """Publish using common env vars set by the pipeline.

    Expected env (Artist Manager provides these when launching DCCs):
        - PIPELINE_PROJECT or PIPELINE_PROJECT_NAME
        - PIPELINE_ASSET or PIPELINE_ASSET_NAME (fallback to current filename stem)
        - PIPELINE_ASSET_TYPE
        - PIPELINE_THUMBNAIL (optional)
        - PIPELINE_DESCRIPTION (optional)
      Other helpful vars that may exist:
        - PIPELINE_TASK_NAME, PIPELINE_TASK_FOLDER, PIPELINE_SCENE_DIR
    """
    project = (
        os.environ.get("PL_PROJECT")
        or os.environ.get("PROJECT")
        or os.environ.get("PIPELINE_PROJECT")
        or os.environ.get("PIPELINE_PROJECT_NAME")
    )
    # Prefer explicit asset name, fall back to task name, finally filename stem
    name = (
        os.environ.get("PL_ASSET")
        or os.environ.get("ASSET")
        or os.environ.get("PIPELINE_ASSET")
        or os.environ.get("PIPELINE_ASSET_NAME")
        or os.environ.get("PL_TASK_NAME")
        or os.environ.get("TASK_NAME")
        or os.environ.get("PIPELINE_TASK_NAME")
    )
    asset_type = (
        os.environ.get("PL_ASSET_TYPE")
        or os.environ.get("ASSET_TYPE")
        or os.environ.get("PIPELINE_ASSET_TYPE")
        or default_asset_type
    )
    description = (
        os.environ.get("PL_DESCRIPTION")
        or os.environ.get("DESCRIPTION")
        or os.environ.get("PIPELINE_DESCRIPTION", "")
    )
    image = (
        os.environ.get("PL_THUMBNAIL")
        or os.environ.get("THUMBNAIL")
        or os.environ.get("PIPELINE_THUMBNAIL")
    )

    # Fallback to current file name if available
    if not name:
        try:
            # Often DCCs set scene path envs; try generic fallbacks
            scene = (
                os.environ.get("HIPFILE")
                or os.environ.get("HIPNAME")
                or os.environ.get("MAYA_FILE")
                or os.environ.get("FILE")
            )
            if scene:
                name = Path(scene).stem
        except Exception:
            pass

    if not (project and name):
        raise ValueError("publish_from_env requires PIPELINE_PROJECT[_NAME] and PIPELINE_ASSET_NAME (or filename)")

    return publish_asset(
        name=name,
        asset_type=asset_type,
        project_name=project,
        description=description,
        image_path=image,
    )


def _main(argv: list[str]) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Publish an asset to the FX3X DB")
    p.add_argument("--name", required=False, help="Asset name")
    p.add_argument("--type", dest="asset_type", required=False, default="prop", help="Asset type")
    p.add_argument("--project", required=False, help="Project name")
    p.add_argument("--description", default="", help="Description")
    p.add_argument("--image", dest="image_path", help="Path to thumbnail/image")
    p.add_argument("--from-env", action="store_true", help="Publish using PIPELINE_* env variables")
    ns = p.parse_args(argv)

    if ns.from_env:
        rec = publish_from_env(default_asset_type=ns.asset_type)
    else:
        if not (ns.name and ns.project):
            p.error("--name and --project are required unless --from-env is used")
        rec = publish_asset(
            name=ns.name,
            asset_type=ns.asset_type,
            project_name=ns.project,
            description=ns.description,
            image_path=ns.image_path,
        )
    print(f"Published asset #{rec.id}: {rec.name} ({rec.asset_type}) in project {rec.project_id}")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
