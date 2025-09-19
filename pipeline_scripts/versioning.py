from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import connection as PGConnection

DEFAULT_TABLE_NAME = "core_scene_file"
TABLE_ENV_VAR = "PIPELINE_SCENE_TABLE"


def get_scene_table_name() -> str:
    return os.environ.get(TABLE_ENV_VAR, DEFAULT_TABLE_NAME)


def _table_identifier(table_name: Optional[str] = None) -> sql.Identifier:
    return sql.Identifier((table_name or get_scene_table_name()).strip())


def ensure_scene_table(conn: PGConnection, table_name: Optional[str] = None) -> None:
    table = (table_name or get_scene_table_name()).strip()
    ident = sql.Identifier(table)
    unique_name = sql.Identifier(f"{table}_uniq")
    task_idx_name = sql.Identifier(f"{table}_task_idx")

    with conn.cursor() as cur:
        cur.execute(
            sql.SQL(
                """
                CREATE TABLE IF NOT EXISTS {table} (
                    id SERIAL PRIMARY KEY,
                    task_id INTEGER NOT NULL REFERENCES core_task(id) ON DELETE CASCADE,
                    artist_id INTEGER NOT NULL REFERENCES core_artist(id) ON DELETE CASCADE,
                    software VARCHAR(32) NOT NULL,
                    file_path TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    iteration INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
                );
                """
            ).format(table=ident)
        )
        cur.execute(
            sql.SQL(
                "ALTER TABLE {table} ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;"
            ).format(table=ident)
        )
        cur.execute(
            sql.SQL(
                "ALTER TABLE {table} ADD COLUMN IF NOT EXISTS iteration INTEGER NOT NULL DEFAULT 1;"
            ).format(table=ident)
        )
        cur.execute(
            sql.SQL(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS {unique_idx}
                ON {table} (task_id, software, version, iteration);
                """
            ).format(unique_idx=unique_name, table=ident)
        )
        cur.execute(
            sql.SQL(
                """
                CREATE INDEX IF NOT EXISTS {task_idx}
                ON {table} (task_id, software, version);
                """
            ).format(task_idx=task_idx_name, table=ident)
        )
    conn.commit()


def fetch_scenes(
    conn: PGConnection,
    task_id: int,
    software: str,
    table_name: Optional[str] = None,
) -> List[Dict[str, object]]:
    ident = _table_identifier(table_name)
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL(
                """
                SELECT id, task_id, artist_id, software, file_path, version, iteration, created_at, updated_at
                FROM {table}
                WHERE task_id = %s AND software = %s
                ORDER BY version DESC, iteration DESC, id DESC;
                """
            ).format(table=ident),
            (task_id, software),
        )
        column_names = [desc[0] for desc in cur.description]
        return [dict(zip(column_names, row)) for row in cur.fetchall()]


def _max_version(
    conn: PGConnection,
    task_id: int,
    software: str,
    table_name: Optional[str] = None,
) -> int:
    ident = _table_identifier(table_name)
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL(
                "SELECT COALESCE(MAX(version), 0) FROM {table} WHERE task_id = %s AND software = %s;"
            ).format(table=ident),
            (task_id, software),
        )
        result = cur.fetchone()
    return int(result[0]) if result and result[0] is not None else 0


def _max_iteration_for_version(
    conn: PGConnection,
    task_id: int,
    software: str,
    version: int,
    table_name: Optional[str] = None,
) -> int:
    if version <= 0:
        return 0
    ident = _table_identifier(table_name)
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL(
                """
                SELECT COALESCE(MAX(iteration), 0)
                FROM {table}
                WHERE task_id = %s AND software = %s AND version = %s;
                """
            ).format(table=ident),
            (task_id, software, version),
        )
        result = cur.fetchone()
    return int(result[0]) if result and result[0] is not None else 0


def next_numbers(
    conn: PGConnection,
    task_id: int,
    software: str,
    bump: str = "iteration",
    table_name: Optional[str] = None,
) -> Tuple[int, int]:
    bump = (bump or "iteration").lower()
    current_version = _max_version(conn, task_id, software, table_name)
    if bump == "version" or current_version == 0:
        next_version = current_version + 1
        return next_version, 1
    latest_iteration = _max_iteration_for_version(conn, task_id, software, current_version, table_name)
    return current_version, (latest_iteration + 1) if latest_iteration else 1


def record_scene(
    conn: PGConnection,
    task_id: int,
    artist_id: int,
    software: str,
    file_path: str,
    version: int,
    iteration: int,
    table_name: Optional[str] = None,
) -> None:
    ident = _table_identifier(table_name)
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL(
                """
                INSERT INTO {table} (task_id, artist_id, software, file_path, version, iteration)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (task_id, software, version, iteration)
                DO UPDATE SET file_path = EXCLUDED.file_path, updated_at = NOW();
                """
            ).format(table=ident),
            (task_id, artist_id, software, file_path, version, iteration),
        )
    conn.commit()


def touch_scene_record(
    conn: PGConnection,
    scene_id: int,
    table_name: Optional[str] = None,
) -> None:
    if not scene_id:
        return
    ident = _table_identifier(table_name)
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("UPDATE {table} SET updated_at = NOW() WHERE id = %s;").format(table=ident),
            (scene_id,),
        )
    conn.commit()


def format_version_label(version: Optional[int]) -> str:
    value = int(version or 0)
    return f"v{value:03d}"


def format_iteration_label(iteration: Optional[int]) -> str:
    value = int(iteration or 0)
    return f"i{value:03d}"
