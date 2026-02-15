from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main() -> int:
    api_base = (os.environ.get("API_BASE_URL") or "http://127.0.0.1:8002").rstrip("/")
    url = f"{api_base}/api/publishes/"
    token = (os.environ.get("PM_API_TOKEN") or "").strip()

    # Defaults are demo-friendly; set DEMO_TASK_ID / DEMO_TARGET_ID to match your DB.
    payload = {
        "task_id": int(os.environ.get("DEMO_TASK_ID", "1")),
        "target_type": os.environ.get("DEMO_TARGET_TYPE", "shot"),
        "target_id": int(os.environ.get("DEMO_TARGET_ID", "1")),
        "software": "houdini",
        "source_version": int(os.environ.get("DEMO_VERSION", "1")),
        "source_iteration": int(os.environ.get("DEMO_ITERATION", "1")),
        "item_usd_path": "/show/sequences/010/0010/fx/houdini/scenes/artist01/task01/usd/asset01/part01/data/part01_v001_i001.usd",
        "asset_usd_path": "/show/sequences/010/0010/fx/houdini/scenes/artist01/task01/usd/asset01/part01/part01.usd",
        "status": "published",
        "metadata": {
            "asset_name": "asset01",
            "part_name": "part01",
            "source": "demo_api_publish",
        },
    }

    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-PM-Token"] = token

    request = Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urlopen(request, timeout=20) as response:  # nosec - local dev endpoint
            status_code = getattr(response, "status", 200)
            body = response.read().decode("utf-8", errors="replace")
            print(f"status={status_code}")
            print(body)
            return 0
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        print(f"status={exc.code}")
        print(details)
        return 1
    except URLError as exc:
        print("status=connection_error")
        print(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

