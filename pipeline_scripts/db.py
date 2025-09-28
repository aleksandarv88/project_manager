import os
from contextlib import contextmanager
from typing import Dict

import psycopg2

REQUIRED_DB_VARS = [
    ("DB_NAME", "PIPELINE_DB_NAME", "dbname"),
    ("DB_USER", "PIPELINE_DB_USER", "user"),
    ("DB_PASSWORD", "PIPELINE_DB_PASSWORD", "password"),
    ("DB_HOST", "PIPELINE_DB_HOST", "host"),
    ("DB_PORT", "PIPELINE_DB_PORT", "port"),
]


def get_db_params_from_env() -> Dict[str, str]:
    params: Dict[str, str] = {}
    missing = []
    for short_key, legacy_key, param_key in REQUIRED_DB_VARS:
        value = os.environ.get(short_key) or os.environ.get(legacy_key)
        if value is None or value == "":
            missing.append(f"{short_key}/{legacy_key}")
            continue
        params[param_key] = value
    if missing:
        raise RuntimeError(
            "Missing database environment variables: {}".format(", ".join(missing))
        )
    return params


@contextmanager
def connection_from_env():
    params = get_db_params_from_env()
    conn = psycopg2.connect(**params)
    try:
        yield conn
    finally:
        conn.close()
