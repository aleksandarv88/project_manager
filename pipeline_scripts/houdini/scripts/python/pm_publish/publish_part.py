def save_asset():
    import os
    import json
    import hou
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError

    node = hou.pwd()

    # 1) Save first (your existing button)
    hou.parm("./lopnet1/save_part_usd/execute").pressButton()

    # ---------- helpers ----------
    def get_str(name):
        p = node.parm(name)
        if p is None:
            raise RuntimeError("Missing parm: {}".format(name))
        try:
            return (p.evalAsString() or "").strip()
        except Exception:
            return str(p.eval()).strip()

    def get_int(name, default=None):
        p = node.parm(name)
        if p is None:
            return default
        try:
            return int(p.eval())
        except Exception:
            return default

    def as_posix(p):
        return os.path.normpath(str(p)).replace("\\", "/")

    def json_safe(x):
        if isinstance(x, set):
            return list(x)
        if isinstance(x, dict):
            return {k: json_safe(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [json_safe(v) for v in x]
        return x

    def newest_usd_in(folder, startswith=None):
        if not os.path.isdir(folder):
            return ""
        best = ("", -1.0)
        for f in os.listdir(folder):
            lf = f.lower()
            if not lf.endswith((".usd", ".usda", ".usdc")):
                continue
            if startswith and not f.startswith(startswith):
                continue
            full = os.path.join(folder, f)
            try:
                m = os.path.getmtime(full)
            except OSError:
                m = -1.0
            if m > best[1]:
                best = (full, m)
        return best[0]

    # ---------- HDA parms ----------
    shot_root = get_str("shot_root")
    show_name = get_str("show_name")
    seq      = get_str("seq")
    shot     = get_str("shot")
    dep_str  = get_str("dep_str")   # DEPT
    task     = get_str("task")      # TASK
    artist   = get_str("artist")    # ARTIST
    asset    = get_str("asset")     # ASSET
    fx_layer = get_str("fx_layer")  # PART
    fx_type  = get_str("fx_type")   # keep for metadata
    ver      = get_int("ver", None)
    itr      = get_int("iter", None)

    if not all([shot_root, show_name, seq, shot, dep_str, task, artist, asset, fx_layer]):
        raise RuntimeError("One or more required parms are empty.")

    # ---------- latest layout paths ----------
    # Task workspace root:
    task_root = os.path.join(
        shot_root, show_name,
        "sequences", seq, shot,
        dep_str,
        "houdini", "scenes",
        artist, task
    )

    # Part folder:
    part_dir = os.path.join(task_root, "usd", asset, fx_layer)
    data_dir = os.path.join(part_dir, "data")

    # Stable part layer:
    stable_part_path = os.path.join(part_dir, "{}.usd".format(fx_layer))

    # Versioned item layer:
    if ver is not None and itr is not None:
        item_path_expected = os.path.join(
            data_dir, "{}_v{:03d}_i{:03d}.usd".format(fx_layer, ver, itr)
        )
    else:
        item_path_expected = ""

    # ---------- resolve actual files on disk ----------
    # 1) Stable (prefer exact name; else newest usd in part_dir)
    if os.path.isfile(stable_part_path):
        part_usd_path = stable_part_path
    else:
        part_usd_path = newest_usd_in(part_dir)  # fallback
        if not part_usd_path:
            raise RuntimeError(
                "Stable PART USD not found.\n"
                "Expected: {}\n"
                "Searched folder: {}".format(stable_part_path, part_dir)
            )

    # 2) Item (prefer exact expected; else newest usd in data_dir; else newest in part_dir)
    if item_path_expected and os.path.isfile(item_path_expected):
        item_usd_path = item_path_expected
    else:
        item_usd_path = newest_usd_in(data_dir, startswith=fx_layer) or newest_usd_in(data_dir) or newest_usd_in(part_dir)
        if not item_usd_path:
            raise RuntimeError(
                "Versioned ITEM USD not found.\n"
                "Expected: {}\n"
                "Searched data folder: {}\n"
                "Searched part folder: {}".format(item_path_expected or "<no ver/iter>", data_dir, part_dir)
            )

    # ---------- API/env ----------
    task_id = (os.environ.get("PM_TASK_ID") or os.environ.get("PIPELINE_TASK_ID") or "").strip()
    if not task_id.isdigit():
        raise RuntimeError("Missing/invalid PM_TASK_ID (or PIPELINE_TASK_ID).")

    api_url = (os.environ.get("PM_API_URL") or "http://127.0.0.1:8002/api/publishes/").strip()
    api_token = (os.environ.get("PM_API_TOKEN") or "").strip()

    # ---------- payload ----------
    payload = {
        "task_id": int(task_id),
        "asset_name": asset,
        "part_name": fx_layer,
        "item_usd_path": as_posix(item_usd_path),
        "asset_usd_path": as_posix(part_usd_path),  # backend expects this key
        "part_usd_path": as_posix(part_usd_path),   # forward compatibility
        "artist": (os.environ.get("PM_ARTIST") or artist),
        "status": "published",
        "bump": "iteration",
        "metadata": {
            "seq": seq,
            "shot": shot,
            "dep_str": dep_str,
            "task": task,
            "asset": asset,
            "fx_type": fx_type,
            "fx_layer": fx_layer,
            "task_root": as_posix(task_root),
            "part_dir": as_posix(part_dir),
            "source": "houdini_hda_publish",
        },
    }

    # keep source save context if you have it
    payload["source_version"] = ver
    payload["source_iteration"] = itr

    payload = json_safe(payload)

    headers = {"Content-Type": "application/json"}
    if api_token:
        headers["Authorization"] = "Bearer {}".format(api_token)
        headers["X-PM-Token"] = api_token

    req = Request(
        api_url,
        data=json.dumps(payload, default=str).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    # ---------- request ----------
    try:
        with urlopen(req, timeout=20) as resp:
            code = int(getattr(resp, "status", 200))
            raw = resp.read().decode("utf-8", errors="replace")
    except HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError("PM publish API failed (HTTP {}): {}".format(e.code, detail))
    except URLError as e:
        raise RuntimeError("PM publish API connection failed: {}".format(e))

    if code not in (200, 201):
        raise RuntimeError("PM publish API failed (HTTP {}): {}".format(code, raw))

    try:
        data = json.loads(raw)
    except Exception:
        raise RuntimeError("PM publish API returned non-JSON: {}".format(raw))

    publish_id = None
    if isinstance(data, dict) and data.get("ok") is True:
        d = data.get("data")
        if isinstance(d, dict):
            publish_id = d.get("publish_id") or d.get("id")
        elif isinstance(d, list) and d and isinstance(d[0], dict):
            # your API sometimes returns list; take first id
            publish_id = d[0].get("id")

    if not publish_id:
        raise RuntimeError("PM publish API response missing publish_id: {}".format(data))

    hou.ui.displayMessage("DB publish registered. ID: {}".format(int(publish_id)))
    return int(publish_id)
