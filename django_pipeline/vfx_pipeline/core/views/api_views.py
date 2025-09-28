from __future__ import annotations

import json
from typing import Any, Dict, Optional

from django.db import connection, models
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt

from core.models import Project, Asset, Sequence, Shot, Task, Artist


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


# -------- Projects --------
@csrf_exempt
def api_projects(request: HttpRequest):
    params = _params(request)
    if request.method == "GET":
        project_id = params.get("id")
        name = params.get("name")
        qs = Project.objects.all()
        if project_id:
            qs = qs.filter(id=project_id)
        if name:
            qs = qs.filter(name=name)
        data = list(qs.values("id", "name", "base_path"))
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
        proj.name = name
        if base_path:
            proj.base_path = base_path
        proj.save()
    else:
        proj, _ = Project.objects.get_or_create(name=name, defaults={"base_path": base_path or Project._meta.get_field("base_path").default})
    return _ok({"id": proj.id, "name": proj.name, "base_path": proj.base_path})


# -------- Assets --------
@csrf_exempt
def api_assets(request: HttpRequest):
    params = _params(request)
    if request.method == "GET":
        asset_id = params.get("id")
        project_id = params.get("project_id")
        qs = Asset.objects.select_related("project").all()
        if asset_id:
            qs = qs.filter(id=asset_id)
        if project_id:
            qs = qs.filter(project_id=project_id)
        data = list(qs.values("id", "name", "asset_type", "project_id"))
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
        asset.project_id = int(project_id)
        asset.name = name
        asset.asset_type = asset_type
        asset.save()
    else:
        asset, _created = Asset.objects.get_or_create(
            project_id=int(project_id), name=name, defaults={"asset_type": asset_type}
        )
        if not _created:
            # update asset_type if provided
            if asset_type:
                asset.asset_type = asset_type
                asset.save()
    return _ok({"id": asset.id, "name": asset.name, "asset_type": asset.asset_type, "project_id": asset.project_id})


# -------- Sequences --------
@csrf_exempt
def api_sequences(request: HttpRequest):
    params = _params(request)
    if request.method == "GET":
        project_id = params.get("project_id")
        if not project_id:
            return _ok([])
        sequences = Sequence.objects.filter(project_id=project_id).values("id", "name", "project_id")
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
        seq.project_id = int(project_id)
        seq.name = name
        seq.save()
    else:
        seq, _ = Sequence.objects.get_or_create(project_id=int(project_id), name=name)
    return _ok({"id": seq.id, "name": seq.name, "project_id": seq.project_id})


# -------- Shots --------
@csrf_exempt
def api_shots(request: HttpRequest):
    params = _params(request)
    if request.method == "GET":
        sequence_id = params.get("sequence_id")
        project_id = params.get("project_id")
        qs = Shot.objects.select_related("sequence").all()
        if sequence_id:
            qs = qs.filter(sequence_id=sequence_id)
        if project_id:
            qs = qs.filter(project_id=project_id)
        data = list(qs.values("id", "name", "sequence_id", "project_id"))
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
        shot.project_id = int(project_id)
        shot.sequence_id = int(sequence_id)
        shot.name = name
        shot.save()
    else:
        shot, _ = Shot.objects.get_or_create(project_id=int(project_id), sequence_id=int(sequence_id), name=name)
    return _ok({"id": shot.id, "name": shot.name, "sequence_id": shot.sequence_id, "project_id": shot.project_id})


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
                "description",
                "status",
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
        "status": (params.get("status") or "not_started").strip() or "not_started",
        "description": (params.get("description") or "").strip(),
    }
    # relationship: asset or sequence/shot
    asset_id = params.get("asset_id")
    sequence_id = params.get("sequence_id")
    shot_id = params.get("shot_id")
    if tid:
        task = Task.objects.filter(id=tid).first()
        if not task:
            return _err("Task not found", status=404)
        task.artist_id = int(artist_id)
        task.task_name = fields["task_name"]
        task.task_type = fields["task_type"]
        task.status = fields["status"]
        task.description = fields["description"]
        task.asset_id = int(asset_id) if asset_id else None
        task.sequence_id = int(sequence_id) if sequence_id else None
        task.shot_id = int(shot_id) if shot_id else None
        task.full_clean()
        task.save()
    else:
        task = Task(
            artist_id=int(artist_id),
            task_name=fields["task_name"],
            task_type=fields["task_type"],
            status=fields["status"],
            description=fields["description"],
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
        "status": task.status,
        "description": task.description,
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




