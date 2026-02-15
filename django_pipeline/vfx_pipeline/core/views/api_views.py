from __future__ import annotations

import json
import os
from pathlib import Path
from decimal import Decimal
from typing import Any, Dict, Optional

from django.contrib.contenttypes.models import ContentType
from django.db import connection, models
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date
from django.utils import timezone

from core.models import (
    Project,
    Asset,
    Sequence,
    Shot,
    Task,
    Artist,
    Tag,
    AssetTag,
    ShotTag,
    SequenceTag,
    Publish,
    PublishComponent,
    VersionLink,
)


def _ok(data: Any = None, status: int = 200):
    return JsonResponse({"ok": True, "data": data}, status=status, safe=False)


def _err(message: str, *, status: int = 400, extra: Optional[Dict[str, Any]] = None):
    payload: Dict[str, Any] = {"ok": False, "error": message}
    if extra:
        payload.update(extra)
    return JsonResponse(payload, status=status)


def _params(request: HttpRequest) -> Dict[str, Any]:
    if request.method == "GET":
        return {k: v for k, v in request.GET.items()}
    # Try form-encoded first
    if request.POST:
        return {k: v for k, v in request.POST.items()}
    # Fallback to JSON
    try:
        body = request.body.decode("utf-8") if request.body else ""
        if body:
            return json.loads(body)
    except Exception:
        pass
    return {}


def _parse_decimal(value: Optional[str], default: Optional[Decimal] = None) -> Optional[Decimal]:
    if value in (None, ""):
        return default
    try:
        return Decimal(str(value))
    except Exception:
        return default


def _parse_int(value: Optional[str], default: Optional[int] = None) -> Optional[int]:
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_metadata(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value:
        try:
            return json.loads(value)
        except Exception:
            return {}
    return {}


def _normalize_file_path(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        normalized = os.path.normpath(raw)
    except Exception:
        normalized = raw
    return Path(normalized).as_posix()


def _is_local_request(request: HttpRequest) -> bool:
    remote_addr = (request.META.get("REMOTE_ADDR") or "").strip()
    try:
        host = (request.get_host() or "").split(":")[0].strip().lower()
    except Exception:
        host = ""
    return remote_addr in {"127.0.0.1", "::1", "localhost"} or host in {"127.0.0.1", "localhost"}


def _has_valid_pm_token(request: HttpRequest) -> bool:
    expected = (os.environ.get("PM_API_TOKEN") or "").strip()
    if not expected:
        return False
    provided = (
        request.headers.get("X-PM-Token")
        or request.headers.get("Authorization", "").replace("Bearer ", "", 1)
    )
    return str(provided or "").strip() == expected


# -------- Projects --------
@csrf_exempt
def api_projects(request: HttpRequest):
    params = _params(request)
    if request.method == "GET":
        project_id = params.get("id")
        code = params.get("code")
        name = params.get("name")
        qs = Project.objects.all()
        if project_id:
            qs = qs.filter(id=project_id)
        if code:
            qs = qs.filter(code=code)
        if name:
            qs = qs.filter(name=name)
        data = list(
            qs.values(
                "id",
                "name",
                "code",
                "description",
                "status",
                "base_path",
                "start_date",
                "due_date",
                "default_fps",
                "resolution_width",
                "resolution_height",
                "color_space",
                "delivery_notes",
            )
        )
        return _ok(data)
    # POST create/update
    name = (params.get("name") or "").strip()
    if not name:
        return _err("Missing name")
    base_path = (params.get("base_path") or "").strip() or None
    pid = params.get("id")
    if pid:
        proj = Project.objects.filter(id=pid).first()
        if not proj:
            return _err("Project not found", status=404)
    else:
        proj = Project(name=name)

    proj.name = name
    if base_path:
        proj.base_path = base_path
    for attr in [
        "code",
        "description",
        "status",
        "color_space",
        "delivery_notes",
    ]:
        if attr in params:
            setattr(proj, attr, (params.get(attr) or "").strip())
    if "start_date" in params:
        proj.start_date = parse_date(params.get("start_date"))
    if "due_date" in params:
        proj.due_date = parse_date(params.get("due_date"))
    if "default_fps" in params:
        proj.default_fps = _parse_decimal(params.get("default_fps"), proj.default_fps) or proj.default_fps
    if "resolution_width" in params:
        proj.resolution_width = _parse_int(params.get("resolution_width"), proj.resolution_width) or proj.resolution_width
    if "resolution_height" in params:
        proj.resolution_height = _parse_int(params.get("resolution_height"), proj.resolution_height) or proj.resolution_height
    proj.save()
    return _ok(
        {
            "id": proj.id,
            "name": proj.name,
            "code": proj.code,
            "status": proj.status,
            "base_path": proj.base_path,
            "start_date": proj.start_date,
            "due_date": proj.due_date,
            "default_fps": proj.default_fps,
            "resolution_width": proj.resolution_width,
            "resolution_height": proj.resolution_height,
            "color_space": proj.color_space,
            "delivery_notes": proj.delivery_notes,
        }
    )


# -------- Assets --------
@csrf_exempt
def api_assets(request: HttpRequest):
    params = _params(request)
    if request.method == "GET":
        asset_id = params.get("id")
        project_id = params.get("project_id")
        code = params.get("code")
        qs = Asset.objects.select_related("project").all()
        if asset_id:
            qs = qs.filter(id=asset_id)
        if project_id:
            qs = qs.filter(project_id=project_id)
        if code:
            qs = qs.filter(code=code)
        data = list(
            qs.values(
                "id",
                "name",
                "code",
                "asset_type",
                "category",
                "subtype",
                "status",
                "pipeline_step",
                "project_id",
                "description",
                "frame_start",
                "frame_end",
                "fps",
            )
        )
        return _ok(data)
    # POST create/update
    project_id = params.get("project_id")
    name = (params.get("name") or "").strip()
    asset_type = (params.get("asset_type") or "other").strip() or "other"
    if not (project_id and name):
        return _err("Missing project_id or name")
    aid = params.get("id")
    if aid:
        asset = Asset.objects.filter(id=aid).first()
        if not asset:
            return _err("Asset not found", status=404)
    else:
        asset = Asset(project_id=int(project_id))
    asset.name = name
    asset.asset_type = asset_type
    for attr in ["code", "category", "subtype", "status", "pipeline_step", "description"]:
        if attr in params:
            setattr(asset, attr, (params.get(attr) or "").strip())
    if "frame_start" in params:
        asset.frame_start = _parse_int(params.get("frame_start"))
    if "frame_end" in params:
        asset.frame_end = _parse_int(params.get("frame_end"))
    if "fps" in params:
        asset.fps = _parse_decimal(params.get("fps"), asset.fps)
    asset.project_id = int(project_id)
    asset.save()
    return _ok(
        {
            "id": asset.id,
            "name": asset.name,
            "code": asset.code,
            "asset_type": asset.asset_type,
            "category": asset.category,
            "subtype": asset.subtype,
            "status": asset.status,
            "pipeline_step": asset.pipeline_step,
            "project_id": asset.project_id,
            "description": asset.description,
            "frame_start": asset.frame_start,
            "frame_end": asset.frame_end,
            "fps": asset.fps,
        }
    )


@csrf_exempt
def api_tags(request: HttpRequest):
    params = _params(request)
    if request.method == "GET":
        qs = Tag.objects.all()
        if params.get("id"):
            qs = qs.filter(id=params.get("id"))
        if params.get("name"):
            qs = qs.filter(name__iexact=params.get("name"))
        if params.get("category"):
            qs = qs.filter(category__iexact=params.get("category"))
        return _ok(list(qs.values("id", "name", "category", "description", "color")))

    name = (params.get("name") or "").strip()
    if not name:
        return _err("Missing name")
    tag_id = params.get("id")
    if tag_id:
        tag = Tag.objects.filter(id=tag_id).first()
        if not tag:
            return _err("Tag not found", status=404)
    else:
        tag = Tag(name=name)
    tag.name = name
    tag.category = (params.get("category") or "").strip()
    tag.description = (params.get("description") or "").strip()
    tag.color = (params.get("color") or "").strip()
    tag.save()
    return _ok({"id": tag.id, "name": tag.name, "category": tag.category, "color": tag.color})


# -------- Sequences --------
@csrf_exempt
def api_sequences(request: HttpRequest):
    params = _params(request)
    if request.method == "GET":
        project_id = params.get("project_id")
        code = params.get("code")
        qs = Sequence.objects.select_related("project").all()
        if project_id:
            qs = qs.filter(project_id=project_id)
        if code:
            qs = qs.filter(code=code)
        sequences = qs.values(
            "id",
            "name",
            "code",
            "description",
            "status",
            "project_id",
            "frame_start",
            "frame_end",
            "handles",
            "fps",
            "resolution_width",
            "resolution_height",
            "color_space",
        )
        return _ok(list(sequences))
    # POST create/update
    project_id = params.get("project_id")
    name = (params.get("name") or "").strip()
    if not (project_id and name):
        return _err("Missing project_id or name")
    sid = params.get("id")
    if sid:
        seq = Sequence.objects.filter(id=sid).first()
        if not seq:
            return _err("Sequence not found", status=404)
    else:
        seq = Sequence(project_id=int(project_id))
    seq.project_id = int(project_id)
    seq.name = name
    for attr in ["code", "description", "status", "color_space"]:
        if attr in params:
            setattr(seq, attr, (params.get(attr) or "").strip())
    if "frame_start" in params:
        seq.frame_start = _parse_int(params.get("frame_start"), seq.frame_start) or seq.frame_start
    if "frame_end" in params:
        seq.frame_end = _parse_int(params.get("frame_end"), seq.frame_end) or seq.frame_end
    if "handles" in params:
        seq.handles = _parse_int(params.get("handles"), seq.handles) or seq.handles
    if "fps" in params:
        seq.fps = _parse_decimal(params.get("fps"), seq.fps) or seq.fps
    if "resolution_width" in params:
        seq.resolution_width = _parse_int(params.get("resolution_width"), seq.resolution_width)
    if "resolution_height" in params:
        seq.resolution_height = _parse_int(params.get("resolution_height"), seq.resolution_height)
    seq.save()
    return _ok(
        {
            "id": seq.id,
            "name": seq.name,
            "code": seq.code,
            "project_id": seq.project_id,
            "status": seq.status,
            "frame_start": seq.frame_start,
            "frame_end": seq.frame_end,
            "handles": seq.handles,
            "fps": seq.fps,
            "resolution_width": seq.resolution_width,
            "resolution_height": seq.resolution_height,
            "color_space": seq.color_space,
        }
    )


# -------- Shots --------
@csrf_exempt
def api_shots(request: HttpRequest):
    params = _params(request)
    if request.method == "GET":
        sequence_id = params.get("sequence_id")
        project_id = params.get("project_id")
        code = params.get("code")
        qs = Shot.objects.select_related("sequence").all()
        if sequence_id:
            qs = qs.filter(sequence_id=sequence_id)
        if project_id:
            qs = qs.filter(project_id=project_id)
        if code:
            qs = qs.filter(code=code)
        data = list(
            qs.values(
                "id",
                "name",
                "code",
                "sequence_id",
                "project_id",
                "status",
                "frame_start",
                "frame_end",
                "handles",
                "fps",
                "cut_in",
                "cut_out",
                "resolution_width",
                "resolution_height",
                "color_space",
                "shot_type",
                "notes",
            )
        )
        return _ok(data)
    # POST create/update
    project_id = params.get("project_id")
    sequence_id = params.get("sequence_id")
    name = (params.get("name") or "").strip()
    if not (project_id and sequence_id and name):
        return _err("Missing project_id, sequence_id or name")
    shid = params.get("id")
    if shid:
        shot = Shot.objects.filter(id=shid).first()
        if not shot:
            return _err("Shot not found", status=404)
    else:
        shot = Shot(project_id=int(project_id), sequence_id=int(sequence_id))
    shot.project_id = int(project_id)
    shot.sequence_id = int(sequence_id)
    shot.name = name
    for attr in ["code", "description", "status", "color_space", "shot_type", "notes"]:
        if attr in params:
            setattr(shot, attr, (params.get(attr) or "").strip())
    for attr in ["frame_start", "frame_end", "handles", "cut_in", "cut_out", "resolution_width", "resolution_height"]:
        if attr in params:
            setattr(shot, attr, _parse_int(params.get(attr)))
    if "fps" in params:
        shot.fps = _parse_decimal(params.get("fps"), shot.fps)
    shot.save()
    return _ok(
        {
            "id": shot.id,
            "name": shot.name,
            "code": shot.code,
            "sequence_id": shot.sequence_id,
            "project_id": shot.project_id,
            "status": shot.status,
            "frame_start": shot.frame_start,
            "frame_end": shot.frame_end,
            "handles": shot.handles,
            "fps": shot.fps,
            "cut_in": shot.cut_in,
            "cut_out": shot.cut_out,
        }
    )


# -------- Artists --------
@csrf_exempt
def api_artists(request: HttpRequest):
    params = _params(request)
    if request.method == "GET":
        aid = params.get("id")
        username = params.get("username")
        qs = Artist.objects.all()
        if aid:
            qs = qs.filter(id=aid)
        if username:
            qs = qs.filter(username=username)
        return _ok(list(qs.values("id", "username", "email", "country", "status")))
    # POST create/update minimal fields
    username = (params.get("username") or "").strip()
    if not username:
        return _err("Missing username")
    aid = params.get("id")
    defaults = {k: (params.get(k) or "").strip() or None for k in ("email", "country", "status")}
    if aid:
        artist = Artist.objects.filter(id=aid).first()
        if not artist:
            return _err("Artist not found", status=404)
        artist.username = username
        if defaults.get("email") is not None:
            artist.email = defaults["email"]
        if defaults.get("country") is not None:
            artist.country = defaults["country"]
        if defaults.get("status") is not None:
            artist.status = defaults["status"]
        artist.save()
    else:
        artist, _ = Artist.objects.get_or_create(username=username, defaults=defaults)
    return _ok({"id": artist.id, "username": artist.username, "email": artist.email, "country": artist.country, "status": artist.status})


# -------- Tasks --------
@csrf_exempt
def api_tasks(request: HttpRequest):
    params = _params(request)
    if request.method == "GET":
        qs = Task.objects.select_related("artist", "asset", "sequence", "shot").all()
        for key in ("artist_id", "asset_id", "sequence_id", "shot_id", "project_id"):
            value = params.get(key)
            if value:
                if key == "project_id":
                    qs = qs.filter(
                        models.Q(asset__project_id=value) | models.Q(sequence__project_id=value) | models.Q(shot__project_id=value)
                    )
                else:
                    qs = qs.filter(**{key: value})
        data = list(
            qs.values(
                "id",
                "artist_id",
                "asset_id",
                "sequence_id",
                "shot_id",
                "task_name",
                "task_type",
                "department",
                "description",
                "notes",
                "status",
                "priority",
                "start_date",
                "due_date",
                "bid_hours",
                "actual_hours",
            )
        )
        return _ok(data)
    # POST create/update
    artist_id = params.get("artist_id")
    task_type = (params.get("task_type") or "").strip()
    if not (artist_id and task_type):
        return _err("Missing artist_id or task_type")
    tid = params.get("id")
    fields = {
        "task_name": (params.get("task_name") or "").strip(),
        "task_type": task_type,
        "department": (params.get("department") or "").strip() or task_type,
        "status": (params.get("status") or "not_started").strip() or "not_started",
        "description": (params.get("description") or "").strip(),
        "notes": (params.get("notes") or "").strip(),
        "priority": _parse_int(params.get("priority"), 50) or 50,
        "start_date": parse_date(params.get("start_date")) if params.get("start_date") else None,
        "due_date": parse_date(params.get("due_date")) if params.get("due_date") else None,
        "bid_hours": _parse_decimal(params.get("bid_hours")),
        "actual_hours": _parse_decimal(params.get("actual_hours")),
    }
    # relationship: asset or sequence/shot
    asset_id = params.get("asset_id")
    sequence_id = params.get("sequence_id")
    shot_id = params.get("shot_id")
    if tid:
        task = Task.objects.filter(id=tid).first()
        if not task:
            return _err("Task not found", status=404)
        task.artist_id = int(artist_id) if artist_id else None
        task.task_name = fields["task_name"]
        task.task_type = fields["task_type"]
        task.department = fields["department"]
        task.status = fields["status"]
        task.description = fields["description"]
        task.notes = fields["notes"]
        task.priority = fields["priority"]
        task.start_date = fields["start_date"]
        task.due_date = fields["due_date"]
        task.bid_hours = fields["bid_hours"]
        task.actual_hours = fields["actual_hours"]
        task.asset_id = int(asset_id) if asset_id else None
        task.sequence_id = int(sequence_id) if sequence_id else None
        task.shot_id = int(shot_id) if shot_id else None
        task.full_clean()
        task.save()
    else:
        task = Task(
            artist_id=int(artist_id) if artist_id else None,
            task_name=fields["task_name"],
            task_type=fields["task_type"],
            department=fields["department"],
            status=fields["status"],
            description=fields["description"],
            notes=fields["notes"],
            priority=fields["priority"],
            start_date=fields["start_date"],
            due_date=fields["due_date"],
            bid_hours=fields["bid_hours"],
            actual_hours=fields["actual_hours"],
            asset_id=int(asset_id) if asset_id else None,
            sequence_id=int(sequence_id) if sequence_id else None,
            shot_id=int(shot_id) if shot_id else None,
        )
        task.full_clean()
        task.save()
    return _ok({
        "id": task.id,
        "artist_id": task.artist_id,
        "asset_id": task.asset_id,
        "sequence_id": task.sequence_id,
        "shot_id": task.shot_id,
        "task_name": task.task_name,
        "task_type": task.task_type,
        "department": task.department,
        "status": task.status,
        "description": task.description,
        "notes": task.notes,
        "priority": task.priority,
        "start_date": task.start_date,
        "due_date": task.due_date,
        "bid_hours": task.bid_hours,
        "actual_hours": task.actual_hours,
    })


# -------- Scenes (versioning) --------
@csrf_exempt
def api_scenes(request: HttpRequest):
    from pipeline_scripts import versioning

    params = _params(request)
    if request.method == "GET":
        task_id = int(params.get("task_id") or 0)
        software = (params.get("software") or "").lower()
        if not (task_id and software):
            return _err("Missing task_id or software")
        # use Django's underlying psycopg2 connection
        versioning.ensure_scene_table(connection.connection)
        rows = versioning.fetch_scenes(connection.connection, task_id, software)
        return _ok(rows)
    return _err("Method not allowed", status=405)


@csrf_exempt
def api_scenes_next(request: HttpRequest):
    from pipeline_scripts import versioning

    params = _params(request)
    task_id = int(params.get("task_id") or 0)
    software = (params.get("software") or "").lower()
    bump = (params.get("bump") or "iteration").lower()
    if not (task_id and software):
        return _err("Missing task_id or software")
    versioning.ensure_scene_table(connection.connection)
    ver, itr = versioning.next_numbers(connection.connection, task_id, software, bump=bump)
    return _ok({"version": ver, "iteration": itr})


@csrf_exempt
def api_scenes_record(request: HttpRequest):
    from pipeline_scripts import versioning

    params = _params(request)
    task_id = int(params.get("task_id") or 0)
    artist_id = int(params.get("artist_id") or 0)
    software = (params.get("software") or "").lower()
    file_path = (params.get("file_path") or "").strip()
    version = int(params.get("version") or 0)
    iteration = int(params.get("iteration") or 0)
    if not all([task_id, artist_id, software, file_path, version, iteration]):
        return _err("Missing required fields")
    versioning.ensure_scene_table(connection.connection)
    versioning.record_scene(connection.connection, task_id, artist_id, software, file_path, version, iteration)
    return _ok({"recorded": True})


TARGET_MAP = {
    "project": Project,
    "sequence": Sequence,
    "shot": Shot,
    "asset": Asset,
}


def _resolve_target(target_type: str, target_id: Optional[str]):
    model = TARGET_MAP.get((target_type or "").lower())
    if not model or not target_id:
        return None, None
    try:
        target = model.objects.get(id=int(target_id))
    except (ValueError, model.DoesNotExist):
        return None, None
    content_type = ContentType.objects.get_for_model(model)
    return content_type, target


def _publish_queryset(target_type: str, target_id: str, task_id: Optional[str], software: Optional[str] = None) -> models.QuerySet:
    content_type, _ = _resolve_target(target_type, target_id)
    if not content_type:
        return Publish.objects.none()
    qs = Publish.objects.filter(target_content_type=content_type, target_object_id=int(target_id))
    if task_id:
        qs = qs.filter(task_id=int(task_id))
    if software:
        qs = qs.filter(software=software)
    return qs


def _next_publish_numbers(qs: models.QuerySet, bump: str) -> tuple[int, int]:
    latest = qs.order_by("-source_version", "-source_iteration", "-id").first()
    if not latest:
        return 1, 1
    current_version = int(latest.source_version or 0)
    current_iteration = int(latest.source_iteration or 0)
    if bump == "version":
        return current_version + 1, 1
    return current_version if current_version > 0 else 1, current_iteration + 1 if current_iteration > 0 else 1


def _sver(value: Optional[int]) -> int:
    return int(value or 0)


def _path_to_posix(value: str) -> str:
    return str(value or "").replace("\\", "/")


def _extract_usd_context(path_value: str) -> Optional[Dict[str, str]]:
    path = _path_to_posix(path_value).strip()
    if not path:
        return None
    parts = [p for p in path.split("/") if p]
    if "sequences" not in parts or "usd" not in parts:
        return None
    seq_idx = parts.index("sequences")
    try:
        seq = parts[seq_idx + 1]
        shot = parts[seq_idx + 2]
        dept = parts[seq_idx + 3]
    except IndexError:
        return None

    artist = ""
    task = ""
    try:
        houdini_idx = parts.index("houdini", seq_idx + 4)
        if parts[houdini_idx + 1] == "scenes":
            artist = parts[houdini_idx + 2]
            task = parts[houdini_idx + 3]
    except Exception:
        pass

    usd_idx = parts.index("usd", seq_idx + 4)
    asset = parts[usd_idx + 1] if len(parts) > usd_idx + 1 else ""
    part = parts[usd_idx + 2] if len(parts) > usd_idx + 2 else ""

    prefix = "/".join(parts[:seq_idx])
    shared_root = "/".join(parts[: seq_idx + 4]) + "/usd"
    asset_layer_path = "/".join(parts[: usd_idx + 2]) + f"/{asset}.usd" if asset else ""
    return {
        "prefix": prefix,
        "seq": seq,
        "shot": shot,
        "dept": dept,
        "artist": artist,
        "task": task,
        "asset": asset,
        "part": part,
        "shared_root": shared_root,
        "asset_layer_path": asset_layer_path,
    }


def _derive_asset_part_and_stable_path(
    asset_usd_path: str,
    item_usd_path: str,
    metadata: Optional[Dict[str, Any]] = None,
    asset_name_hint: Optional[str] = None,
    part_name_hint: Optional[str] = None,
) -> tuple[str, str, str]:
    meta = metadata or {}
    path = _path_to_posix(asset_usd_path or item_usd_path or "")
    parts = [p for p in path.split("/") if p]

    asset_name = str(
        asset_name_hint
        or meta.get("asset_name")
        or meta.get("asset")
        or ""
    ).strip()
    part_name = str(
        part_name_hint
        or meta.get("part_name")
        or meta.get("fx_layer")
        or ""
    ).strip()

    if "usd" in parts:
        usd_idx = parts.index("usd")
        if not asset_name and len(parts) > usd_idx + 1:
            asset_name = parts[usd_idx + 1]
        if not part_name and len(parts) > usd_idx + 2:
            part_name = parts[usd_idx + 2]

    if not part_name and path:
        part_name = Path(path).stem
    if not asset_name:
        asset_name = "unknown_asset"
    if not part_name:
        part_name = "unknown_part"

    if asset_usd_path:
        parent = Path(_path_to_posix(asset_usd_path)).parent
    elif item_usd_path:
        item_parent = Path(_path_to_posix(item_usd_path)).parent
        if item_parent.name.lower() == "data":
            parent = item_parent.parent
        else:
            parent = item_parent
    else:
        parent = Path(".")
    stable_path = _path_to_posix(str(parent / f"{part_name}.usd"))

    return asset_name, part_name, stable_path


def _write_usda_sublayers(layer_path: str, sublayers: list[str]) -> None:
    target = Path(layer_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    unique = []
    seen = set()
    for candidate in sublayers:
        normalized = _path_to_posix(candidate).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique.append(normalized)

    rel_paths = []
    for sub in unique:
        rel = os.path.relpath(sub, str(target.parent)).replace("\\", "/")
        if not rel.startswith("."):
            rel = f"./{rel}"
        rel_paths.append(rel)

    lines = [
        "#usda 1.0",
        "(",
        "    subLayers = [",
    ]
    for idx, rel in enumerate(rel_paths):
        comma = "," if idx < len(rel_paths) - 1 else ""
        lines.append(f'        @"{rel}"@{comma}')
    lines.extend(
        [
            "    ]",
            ")",
            "",
        ]
    )
    target.write_text("\n".join(lines), encoding="utf-8")


def _collect_latest_publish_paths(project_id: int, matcher) -> Dict[str, str]:
    latest: Dict[str, tuple[int, int, int, str]] = {}
    qs = Publish.objects.filter(project_id=project_id).exclude(asset_usd_path="")
    for candidate in qs:
        context = _extract_usd_context(candidate.asset_usd_path or "")
        if not context:
            continue
        key = matcher(candidate, context)
        if not key:
            continue
        rank = (
            _sver(candidate.source_version),
            _sver(candidate.source_iteration),
            int(candidate.id or 0),
            _path_to_posix(candidate.asset_usd_path or ""),
        )
        prev = latest.get(key)
        if not prev or rank[:3] > prev[:3]:
            latest[key] = rank
    return {k: v[3] for k, v in latest.items()}


def _rebuild_shared_usd_layers(publish: Publish) -> Optional[str]:
    context = _extract_usd_context(publish.asset_usd_path or "")
    if not context:
        return "Skipped shared layer rebuild: could not parse USD context from asset_usd_path."

    seq = context["seq"]
    shot = context["shot"]
    dept = context["dept"]
    artist = context["artist"]
    asset = context["asset"]
    shared_root = context["shared_root"]
    if not all([seq, shot, dept, artist, asset]):
        return "Skipped shared layer rebuild: missing one or more context fields (seq/shot/dept/artist/asset)."

    # 1) Rebuild asset layer from latest part stable paths (DB authoritative).
    part_paths = _collect_latest_publish_paths(
        publish.project_id,
        lambda p, c: (
            c["part"]
            if c["seq"] == seq
            and c["shot"] == shot
            and c["dept"] == dept
            and c["artist"] == artist
            and c["asset"] == asset
            else ""
        ),
    )
    asset_layer = context["asset_layer_path"]
    if asset_layer and part_paths:
        _write_usda_sublayers(asset_layer, sorted(part_paths.values()))

    # 2) Rebuild artist layer from latest asset layers for the artist context.
    asset_layer_paths = _collect_latest_publish_paths(
        publish.project_id,
        lambda p, c: (
            c["asset"]
            if c["seq"] == seq and c["shot"] == shot and c["dept"] == dept and c["artist"] == artist
            else ""
        ),
    )
    artist_layer_path = f"{shared_root}/artist/{artist}.usd"
    artist_sublayers = []
    for _, stable_part_path in sorted(asset_layer_paths.items()):
        c = _extract_usd_context(stable_part_path)
        if c and c.get("asset_layer_path"):
            artist_sublayers.append(c["asset_layer_path"])
    if artist_sublayers:
        _write_usda_sublayers(artist_layer_path, artist_sublayers)

    # 3) Rebuild dept layer from artist layers.
    artist_names = _collect_latest_publish_paths(
        publish.project_id,
        lambda p, c: (
            c["artist"] if c["seq"] == seq and c["shot"] == shot and c["dept"] == dept and c["artist"] else ""
        ),
    )
    dept_layer_path = f"{shared_root}/dept/{dept}.usd"
    dept_sublayers = [f"{shared_root}/artist/{name}.usd" for name in sorted(artist_names.keys()) if name]
    if dept_sublayers:
        _write_usda_sublayers(dept_layer_path, dept_sublayers)

    # 4) Rebuild shot and seq layers in shared root.
    shot_layer_path = f"{shared_root}/shot/{shot}.usd"
    _write_usda_sublayers(shot_layer_path, [dept_layer_path])
    seq_layer_path = f"{shared_root}/seq/{seq}.usd"
    _write_usda_sublayers(seq_layer_path, [shot_layer_path])
    return None


@csrf_exempt
def api_publishes_next(request: HttpRequest):
    params = _params(request)
    target_type = (params.get("target_type") or "").lower()
    target_id = params.get("target_id")
    task_id = params.get("task_id")
    bump = (params.get("bump") or "iteration").lower()
    software = (params.get("software") or "").strip() or None
    if target_type not in TARGET_MAP or not target_id:
        return _err("Missing or invalid target")
    qs = _publish_queryset(target_type, target_id, task_id, software)
    version, iteration = _next_publish_numbers(qs, bump)
    return _ok({"version": version, "iteration": iteration})


@csrf_exempt
def api_publishes(request: HttpRequest):
    params = _params(request)
    target_type = (params.get("target_type") or "").lower()
    target_id = params.get("target_id")
    task_id = params.get("task_id")

    if request.method == "GET":
        qs = Publish.objects.select_related("task", "created_by").all()
        software_filter = (params.get("software") or "").strip() or None
        latest_per_part = params.get("latest_per_part") in {"1", "true", "True", True}
        asset_filter = (params.get("asset") or params.get("asset_name") or "").strip()
        if task_id:
            qs = qs.filter(task_id=task_id)
        if target_type and target_id:
            qs = _publish_queryset(target_type, target_id, task_id, software_filter)
        if params.get("project_id"):
            qs = qs.filter(project_id=params.get("project_id"))
        if software_filter:
            qs = qs.filter(software=software_filter)

        if latest_per_part:
            latest_map: Dict[str, Dict[str, Any]] = {}
            for publish in qs.order_by("-source_version", "-source_iteration", "-published_at", "-id"):
                meta = publish.metadata if isinstance(publish.metadata, dict) else {}
                asset_name, part_name, stable_path = _derive_asset_part_and_stable_path(
                    publish.asset_usd_path,
                    publish.item_usd_path,
                    metadata=meta,
                )
                if asset_filter and asset_name.lower() != asset_filter.lower():
                    continue
                if not part_name or not stable_path:
                    continue
                key = part_name.lower()
                if key in latest_map:
                    continue
                latest_map[key] = {
                    "part_name": part_name,
                    "part_usd_path": stable_path,
                    "publish_id": publish.id,
                    "asset_name": asset_name,
                }
            data = list(latest_map.values())
            data.sort(key=lambda item: item["part_name"].lower())
            return _ok(data)

        include_components = params.get("include_components") in {"1", "true", "True", True}
        data = []
        for publish in qs.order_by("-published_at"):
            item = {
                "id": publish.id,
                "publish_id": publish.id,
                "project_id": publish.project_id,
                "target_type": publish.target_content_type.model,
                "target_id": publish.target_object_id,
                "task_id": publish.task_id,
                "created_by": publish.created_by_id,
                "software": publish.software,
                "label": publish.label,
                "source_version": publish.source_version,
                "source_iteration": publish.source_iteration,
                # Backward-compatible keys for older clients.
                "version": publish.source_version,
                "iteration": publish.source_iteration,
                "status": publish.status,
                "item_usd_path": publish.item_usd_path,
                "asset_usd_path": publish.asset_usd_path,
                "preview_path": publish.preview_path,
                "comment": publish.comment,
                "metadata": publish.metadata,
                "published_at": publish.published_at,
                "is_latest": publish.is_latest,
            }
            if include_components:
                item["components"] = list(
                    publish.components.values(
                        "id",
                        "name",
                        "component_type",
                        "file_path",
                        "file_size",
                        "hash_md5",
                        "frame_start",
                        "frame_end",
                        "metadata",
                    )
                )
            data.append(item)
        return _ok(data)

    # POST -> create publish
    if not (_is_local_request(request) or _has_valid_pm_token(request)):
        return _err("Forbidden", status=403)

    item_usd_path = _normalize_file_path(params.get("item_usd_path"))
    part_usd_path = _normalize_file_path(params.get("part_usd_path"))
    asset_usd_path = _normalize_file_path(params.get("asset_usd_path") or part_usd_path)
    preview_path = _normalize_file_path(params.get("preview_path"))

    if not task_id:
        return _err("Missing task_id")
    # Backward-compatible behavior:
    # - Existing scene/version saver posts components without item/asset USD fields.
    # - Part-publish flow posts both item_usd_path + asset_usd_path.
    has_item = bool(item_usd_path)
    has_asset = bool(asset_usd_path)
    if has_item ^ has_asset:
        return _err("Provide both item_usd_path and asset_usd_path, or neither.")

    task = None
    if task_id:
        task = Task.objects.select_related(
            "asset__project",
            "shot__project",
            "shot__sequence__project",
            "sequence__project",
        ).filter(id=task_id).first()
        if task and not target_type:
            if task.asset_id:
                target_type = "asset"
                target_id = str(task.asset_id)
            elif task.shot_id:
                target_type = "shot"
                target_id = str(task.shot_id)
            elif task.sequence_id:
                target_type = "sequence"
                target_id = str(task.sequence_id)

    if target_type not in TARGET_MAP or not target_id:
        return _err("Missing or invalid target")

    content_type, target = _resolve_target(target_type, target_id)
    if not target:
        return _err("Target not found", status=404)

    project = getattr(target, "project", None)
    if not project and hasattr(target, "sequence"):
        project = target.sequence.project
    if not project and target_type == "project":
        project = target
    if not project:
        project_id = params.get("project_id")
        if project_id:
            project = Project.objects.filter(id=project_id).first()
    if not project and task:
        if task.asset_id and task.asset and task.asset.project:
            project = task.asset.project
        elif task.shot_id and task.shot:
            project = task.shot.project
        elif task.sequence_id and task.sequence:
            project = task.sequence.project
    if not project:
        return _err("Cannot resolve project for publish", status=400)

    artist = None
    if params.get("artist_id"):
        artist = Artist.objects.filter(id=params.get("artist_id")).first()

    bump = (params.get("bump") or "iteration").lower()
    source_version = _parse_int(
        params.get("source_version")
        or params.get("houdini_version")
        or params.get("dcc_version")
        or params.get("version")
    )
    source_iteration = _parse_int(
        params.get("source_iteration")
        or params.get("houdini_iteration")
        or params.get("dcc_iteration")
        or params.get("iteration")
    )
    if not (source_version and source_iteration):
        qs = _publish_queryset(target_type, target_id, task_id, (params.get("software") or "").strip() or None)
        source_version, source_iteration = _next_publish_numbers(qs, bump)

    metadata = _parse_metadata(params.get("metadata"))
    asset_name, part_name, stable_part_path = _derive_asset_part_and_stable_path(
        asset_usd_path,
        item_usd_path,
        metadata=metadata,
        asset_name_hint=params.get("asset_name"),
        part_name_hint=params.get("part_name"),
    )
    metadata["asset_name"] = asset_name
    metadata["asset"] = asset_name
    metadata["part_name"] = part_name
    metadata["fx_layer"] = part_name

    publish = Publish.objects.create(
        project=project,
        target_content_type=content_type,
        target_object_id=target.id,
        task=task,
        created_by=artist,
        software=(params.get("software") or "").strip(),
        label=(params.get("label") or "").strip(),
        source_version=source_version,
        source_iteration=source_iteration,
        status=(params.get("status") or "pending").strip() or "pending",
        item_usd_path=item_usd_path,
        asset_usd_path=stable_part_path,
        preview_path=preview_path,
        comment=(params.get("comment") or "").strip(),
        metadata=metadata,
        is_latest=True,
        published_at=timezone.now(),
    )

    # Ensure latest flag for the same stream (target + task + software scope).
    latest_qs = Publish.objects.filter(
        target_content_type=content_type,
        target_object_id=target.id,
        task=task,
    )
    if publish.software:
        latest_qs = latest_qs.filter(software=publish.software)
    latest_qs.exclude(id=publish.id).update(is_latest=False)

    components = params.get("components")
    if isinstance(components, str):
        try:
            components = json.loads(components)
        except Exception:
            components = []
    if isinstance(components, list):
        for component in components:
            if not isinstance(component, dict):
                continue
            component_name = component.get("name") or component.get("label") or "main"
            component_type = component.get("component_type", "scene")
            PublishComponent.objects.update_or_create(
                publish=publish,
                name=component_name,
                component_type=component_type,
                defaults={
                    "file_path": component.get("file_path", ""),
                    "file_size": _parse_int(component.get("file_size")),
                    "hash_md5": component.get("hash_md5", ""),
                    "frame_start": _parse_int(component.get("frame_start")),
                    "frame_end": _parse_int(component.get("frame_end")),
                    "metadata": _parse_metadata(component.get("metadata")),
                },
            )
    else:
        components = []

    if item_usd_path:
        PublishComponent.objects.update_or_create(
            publish=publish,
            name="item_usd",
            component_type="data",
            defaults={
                "file_path": item_usd_path,
                "metadata": {"role": "item_usd"},
            },
        )
    if stable_part_path:
        PublishComponent.objects.update_or_create(
            publish=publish,
            name="asset_usd",
            component_type="data",
            defaults={
                "file_path": stable_part_path,
                "metadata": {"role": "asset_usd"},
            },
        )
    if preview_path:
        PublishComponent.objects.update_or_create(
            publish=publish,
            name="preview",
            component_type="preview",
            defaults={
                "file_path": preview_path,
                "metadata": {"role": "preview"},
            },
        )

    links = params.get("links")
    if isinstance(links, str):
        try:
            links = json.loads(links)
        except Exception:
            links = []
    if isinstance(links, list):
        for link in links:
            if not isinstance(link, dict):
                continue
            target_publish_id = link.get("target_publish_id")
            if not target_publish_id:
                continue
            try:
                target_publish = Publish.objects.get(id=int(target_publish_id))
            except (ValueError, Publish.DoesNotExist):
                continue
            VersionLink.objects.get_or_create(
                source=publish,
                target=target_publish,
                link_type=link.get("link_type", "dependency"),
                defaults={"notes": link.get("notes", "")},
            )

    layer_warning = None
    try:
        layer_warning = _rebuild_shared_usd_layers(publish)
    except Exception as exc:
        layer_warning = f"Shared layer rebuild failed: {exc}"

    response_data = {
        "publish_id": publish.id,
        "id": publish.id,
        "source_version": publish.source_version,
        "source_iteration": publish.source_iteration,
        # Backward-compatible keys for older clients.
        "version": publish.source_version,
        "iteration": publish.source_iteration,
        "is_latest": publish.is_latest,
        "part_name": part_name,
        "part_usd_path": stable_part_path,
    }
    if layer_warning:
        response_data["layer_warning"] = layer_warning

    return _ok(response_data, status=201)


