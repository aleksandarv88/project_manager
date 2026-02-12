from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional
from urllib.parse import urlsplit, urlunsplit


def _base_url() -> Optional[str]:
    url = os.environ.get("PIPELINE_API_BASE") or os.environ.get("API_BASE_URL")
    if not url:
        return None
    normalized = url.rstrip("/")
    parts = urlsplit(normalized)
    path = parts.path.rstrip("/")
    if path.endswith("/api"):
        path = path[:-4]
    normalized_parts = (parts.scheme, parts.netloc, path, parts.query, parts.fragment)
    return urlunsplit(normalized_parts).rstrip("/")


def _request(method: str, path: str, params: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    base = _base_url()
    if not base:
        raise RuntimeError("PIPELINE_API_BASE is not set")
    url = f"{base}{path}"
    try:
        import requests  # type: ignore

        if method.upper() == "GET":
            resp = requests.get(url, params=params, timeout=10)
        else:
            # Send as form-encoded by default
            resp = requests.post(url, data=data or params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        # Fallback to stdlib
        from urllib.parse import urlencode
        from urllib.request import Request, urlopen

        if method.upper() == "GET" and params:
            url = url + ("?" + urlencode(params))
            body = None
            headers = {}
        else:
            body = urlencode(data or params or {}).encode("utf-8")
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
        req = Request(url, data=body, headers=headers, method=method.upper())
        with urlopen(req, timeout=15) as resp:  # nosec - internal
            raw = resp.read().decode("utf-8")
            try:
                return json.loads(raw)
            except Exception:
                return {"ok": False, "error": "Invalid JSON response", "raw": raw}


def api_get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return _request("GET", path, params=params)


def api_post(path: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return _request("POST", path, data=data)
