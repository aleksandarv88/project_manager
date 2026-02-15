def build_asset():
    import os, json, hou
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError

    node = hou.pwd()

    # Read asset context from parms on the node (same pattern as you used)
    shot_root = node.parm("shot_root").evalAsString().strip()
    show_name = node.parm("show_name").evalAsString().strip()
    seq      = node.parm("seq").evalAsString().strip()
    shot     = node.parm("shot").evalAsString().strip()
    dep_str  = node.parm("dep_str").evalAsString().strip()
    task     = node.parm("task").evalAsString().strip()
    artist   = node.parm("artist").evalAsString().strip()
    asset    = node.parm("asset").evalAsString().strip()

    # Where the asset root lives in your current layout
    task_root = os.path.join(
        shot_root, show_name,
        "sequences", seq, shot,
        dep_str,
        "houdini", "scenes",
        artist, task
    )
    asset_root = os.path.join(task_root, "usd", asset)
    asset_usd_path = os.path.join(asset_root, "{}.usd".format(asset))

    # API
    api_url = (os.environ.get("PM_API_URL") or "http://127.0.0.1:8002/api/publishes/").strip()
    token   = (os.environ.get("PM_API_TOKEN") or "").strip()

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
        headers["X-PM-Token"] = token

    # Fetch publishes for this asset (server may ignore filter; we filter client-side)
    url = api_url + ("&" if "?" in api_url else "?") + "asset_name=" + asset
    try:
        raw = urlopen(Request(url, headers=headers, method="GET"), timeout=20).read().decode("utf-8", "replace")
    except HTTPError as e:
        raise RuntimeError("GET publishes failed (HTTP {}): {}".format(
            e.code, e.read().decode("utf-8", "replace")
        ))
    except URLError as e:
        raise RuntimeError("GET publishes connection failed: {}".format(e))

    data = json.loads(raw)
    rows = data["data"] if isinstance(data, dict) and "data" in data else data

    # Collect one stable part path per part
    parts = {}  # part_name -> part_usd_path
    for r in rows:
        md = r.get("metadata") or {}
        a = (md.get("asset") or r.get("asset_name") or "").strip()
        if a.lower() != asset.lower():
            continue

        part = (md.get("fx_layer") or r.get("part_name") or "").strip()
        if not part:
            continue

        # Prefer explicit part_usd_path, fallback to asset_usd_path (older backend)
        p = (r.get("part_usd_path") or r.get("asset_usd_path") or "").strip()
        if not p:
            continue

        # Force stable path to "{PART}.usd" under the part folder
        # (prevents random filenames ending up in the asset)
        p_norm = os.path.normpath(p)
        part_dir = os.path.dirname(p_norm)
        stable = os.path.join(part_dir, "{}.usd".format(part))

        # Keep if it exists (for demo clarity)
        if os.path.isfile(stable):
            parts[part] = stable
        elif os.path.isfile(p_norm):
            # if stable doesn't exist but p points to something real, use p (fallback)
            parts[part] = p_norm

    if not parts:
        raise RuntimeError("No parts found in DB for asset '{}'.".format(asset))

    # Deterministic order
    part_paths = [parts[k] for k in sorted(parts.keys())]

    # Write ASSET layer as a sublayer stack
    # (No Houdini node needed; just write USD layer file)
    try:
        from pxr import Sdf
    except Exception as e:
        raise RuntimeError("pxr not available in this Houdini Python. Error: {}".format(e))

    os.makedirs(asset_root, exist_ok=True)

    layer = Sdf.Layer.CreateNew(asset_usd_path)
    if layer is None:
        raise RuntimeError("Failed to create asset layer: {}".format(asset_usd_path))

    # USD stores paths as strings; use forward slashes
    layer.subLayerPaths = [os.path.normpath(p).replace(chr(92), "/") for p in part_paths]
    layer.defaultPrim = ""  # optional; keep empty
    layer.comment = "Auto-built from DB parts for asset '{}'".format(asset)
    layer.Save()

    print("BUILT ASSET USD:", asset_usd_path)
    print("SUBLAYERS:")
    for p in layer.subLayerPaths:
        print("  -", p)

    try:
        hou.ui.displayMessage("Asset built:\n{}".format(asset_usd_path))
    except Exception:
        pass

    return asset_usd_path
