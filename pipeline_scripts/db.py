import os
from contextlib import contextmanager
from typing import Dict

import psycopg2

REQUIRED_DB_VARS = {
    "PIPELINE_DB_NAME": "dbname",
    "PIPELINE_DB_USER": "user",
    "PIPELINE_DB_PASSWORD": "password",
    "PIPELINE_DB_HOST": "host",
    "PIPELINE_DB_PORT": "port",
}


def get_db_params_from_env() -> Dict[str, str]:
    params: Dict[str, str] = {}
    missing = []
    for env_key, param_key in REQUIRED_DB_VARS.items():
        value = os.environ.get(env_key)
        if value is None or value == "":
            missing.append(env_key)
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
