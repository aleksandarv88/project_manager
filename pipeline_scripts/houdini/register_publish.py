from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _normalize_path(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    return Path(os.path.normpath(raw)).as_posix()


def _headers(token: str) -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-PM-Token"] = token
    return headers


def register_publish_to_pm(
    item_usd_path: str,
    asset_usd_path: str,
    version: Optional[int] = None,
    iteration: Optional[int] = None,
    status: str = "published",
) -> int:
    """Register a publish in project_manager Django API and return publish_id."""
    api_url = os.environ.get("PM_API_URL", "http://127.0.0.1:8002/api/publishes/").strip()
    api_token = os.environ.get("PM_API_TOKEN", "").strip()
    task_id = (os.environ.get("PM_TASK_ID") or "").strip()
    project = (os.environ.get("PM_PROJECT") or "").strip()
    sequence = (os.environ.get("PM_SEQ") or "").strip()
    shot = (os.environ.get("PM_SHOT") or "").strip()
    artist = (os.environ.get("PM_ARTIST") or "").strip()

    if not task_id:
        raise RuntimeError("Missing PM_TASK_ID in environment.")

    payload: Dict[str, Any] = {
        "task_id": int(task_id),
        "item_usd_path": _normalize_path(item_usd_path),
        "asset_usd_path": _normalize_path(asset_usd_path),
        "status": status or "published",
        "metadata": {
            "pm_project": project,
            "pm_seq": sequence,
            "pm_shot": shot,
            "pm_artist": artist,
            "source": "houdini_hda",
        },
    }
    if version is not None:
        payload["version"] = int(version)
    if iteration is not None:
        payload["iteration"] = int(iteration)

    body = json.dumps(payload).encode("utf-8")
    request = Request(api_url, data=body, headers=_headers(api_token), method="POST")

    try:
        with urlopen(request, timeout=20) as response:  # nosec - local pipeline service
            status_code = int(getattr(response, "status", 200))
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else str(exc)
        raise RuntimeError(f"Publish API request failed ({exc.code}): {details}") from exc
    except URLError as exc:
        raise RuntimeError(f"Publish API connection failed: {exc}") from exc

    if status_code not in (200, 201):
        raise RuntimeError(f"Publish API request failed ({status_code}): {raw}")

    try:
        data = json.loads(raw)
    except Exception as exc:
        raise RuntimeError(f"Publish API returned non-JSON response: {raw}") from exc

    if not data.get("ok"):
        raise RuntimeError(f"Publish API error: {data}")

    result = data.get("data") or {}
    publish_id = result.get("publish_id") or result.get("id")
    if not publish_id:
        raise RuntimeError(f"Publish API response missing publish_id: {data}")
    return int(publish_id)
