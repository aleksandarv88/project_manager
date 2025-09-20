import json
from urllib.parse import urlencode
from typing import Optional

from django.db.models import Prefetch, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from core.forms import ArtistForm, TaskForm, TaskUpdateForm
from core.models import Artist, Task, Sequence, Project, Asset

FILTER_KEYS = ("project", "sequence", "shot", "asset", "context")


def _extract_filters(params, prefix=""):
    filters = {}
    for key in FILTER_KEYS:
        param_name = f"{prefix}{key}" if prefix else key
        value = params.get(param_name)
        if value is None:
            value = ""
        filters[key] = str(value).strip()
    return filters


def _redirect_with_state(filters, open_artists=""):
    normalized = filters.copy()
    if normalized.get("context") == "shot":
        normalized["context"] = ""
    params = {k: v for k, v in normalized.items() if v}
    if open_artists:
        params["open"] = open_artists
    base_url = reverse("artist_assignment")
    if params:
        return redirect(f"{base_url}?{urlencode(params)}")
    return redirect(base_url)


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def artist_manager(request):
    """Simple page to add artists and manage the roster."""
    status_filter = request.GET.get("status", "active")
    valid_filters = {"active", "inactive", "vacation", "all"}
    if status_filter not in valid_filters:
        status_filter = "active"

    artists_qs = Artist.objects.order_by("username")
    if status_filter != "all":
        artists_qs = artists_qs.filter(status=status_filter)
    artists = list(artists_qs)

    artist_status_choices = Artist.STATUS_CHOICES
    valid_artist_status_values = {choice[0] for choice in artist_status_choices}

    if request.method == "POST":
        status_redirect = request.POST.get("status_filter", status_filter)
        if status_redirect not in valid_filters:
            status_redirect = "active"

        if "delete_artist" in request.POST:
            artist_id = request.POST.get("delete_artist_id")
            if artist_id:
                artist = get_object_or_404(Artist, pk=artist_id)
                artist.delete()
            return redirect(f"{reverse('artist_manager')}?status={status_redirect}")

        if "update_artist_status" in request.POST:
            artist_id = request.POST.get("artist_id")
            new_status = request.POST.get("artist_status")
            if artist_id and new_status in valid_artist_status_values:
                artist = get_object_or_404(Artist, pk=artist_id)
                if artist.status != new_status:
                    artist.status = new_status
                    artist.save(update_fields=["status"])
            return redirect(f"{reverse('artist_manager')}?status={status_redirect}")

        form = ArtistForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect(f"{reverse('artist_manager')}?status={status_redirect}")
    else:
        form = ArtistForm()

    status_choices = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("vacation", "On Vacation"),
        ("all", "All"),
    ]

    return render(
        request,
        "core/artist_manager.html",
        {
            "artist_form": form,
            "artists": artists,
            "status_filter": status_filter,
            "status_choices": status_choices,
            "artist_status_choices": artist_status_choices,
        },
    )


def artist_assignment(request):
    filter_source = request.POST if request.method == "POST" else request.GET
    filter_prefix = "filter_" if request.method == "POST" else ""
    filter_values = _extract_filters(filter_source, prefix=filter_prefix)

    context_key = f"{filter_prefix}context"
    context_present = context_key in filter_source
    context_raw = (filter_values.get("context") or "").strip().lower()
    if context_raw not in {"asset", "shot"}:
        context_filter = "" if context_present else "shot"
    else:
        context_filter = context_raw
    filter_values["context"] = context_filter
    if context_filter != "asset":
        filter_values["asset"] = ""

    project_id = _safe_int(filter_values["project"])
    sequence_id = _safe_int(filter_values["sequence"])
    shot_id = _safe_int(filter_values["shot"])
    asset_id = _safe_int(filter_values["asset"]) if context_filter == "asset" else None

    task_queryset = Task.objects.select_related(
        "asset__project",
        "sequence__project",
        "shot__sequence__project",
    )

    if project_id:
        task_queryset = task_queryset.filter(
            Q(asset__project_id=project_id)
            | Q(sequence__project_id=project_id)
            | Q(shot__sequence__project_id=project_id)
        )

    if context_filter == "asset":
        task_queryset = task_queryset.filter(asset__isnull=False)
        if project_id:
            task_queryset = task_queryset.filter(asset__project_id=project_id)
        if asset_id:
            task_queryset = task_queryset.filter(asset_id=asset_id)
    else:
        if context_filter == "shot":
            task_queryset = task_queryset.filter(asset__isnull=True)
        if sequence_id:
            task_queryset = task_queryset.filter(
                Q(sequence_id=sequence_id) | Q(shot__sequence_id=sequence_id)
            )
        if shot_id:
            task_queryset = task_queryset.filter(shot_id=shot_id)

    task_queryset = task_queryset.order_by("id")
    task_prefetch = Prefetch("tasks", queryset=task_queryset)

    artists_qs = Artist.objects.order_by("username").prefetch_related(task_prefetch)
    artists_list = list(artists_qs)
    filters_active = any([project_id, sequence_id, shot_id, asset_id]) or context_filter in {"asset", "shot"}
    if filters_active:
        artists_list = [artist for artist in artists_list if artist.tasks.all()]

    sequence_queryset = (
        Sequence.objects.select_related("project").prefetch_related("shots").order_by("name")
    )

    project_sequence_map = {}
    sequence_shot_map = {}
    all_sequences = []

    for sequence in sequence_queryset:
        seq_data = {"id": sequence.id, "name": sequence.name}
        all_sequences.append(
            {"id": sequence.id, "name": sequence.name, "project": sequence.project_id}
        )
        project_sequence_map.setdefault(sequence.project_id, []).append(seq_data)
        sequence_shot_map[sequence.id] = [
            {"id": shot.id, "name": shot.name}
            for shot in sorted(sequence.shots.all(), key=lambda s: s.name)
        ]

    project_options = Project.objects.order_by("name")

    asset_queryset = Asset.objects.select_related("project").order_by("name")
    project_asset_map: dict[int, list[dict[str, str]]] = {}
    for asset in asset_queryset:
        if asset.project_id:
            project_asset_map.setdefault(asset.project_id, []).append({"id": asset.id, "name": asset.name})

    if request.method == "POST" and "add_task" in request.POST:
        task_form = TaskForm(request.POST)
        if task_form.is_valid():
            task_form.save()
            open_artists = request.POST.get("open_artists", "")
            return _redirect_with_state(filter_values, open_artists)
    else:
        task_form = TaskForm()

    context = {
        "artists": artists_list,
        "task_form": task_form,
        "department_choices": task_form.fields["task_type"].choices,
        "sequence_shot_json": json.dumps(sequence_shot_map, ensure_ascii=False),
        "project_sequence_json": json.dumps(project_sequence_map, ensure_ascii=False),
        "project_asset_json": json.dumps(project_asset_map, ensure_ascii=False),
        "all_sequences_json": json.dumps(all_sequences, ensure_ascii=False),
        "project_options": project_options,
        "filter_project": filter_values["project"],
        "filter_sequence": filter_values["sequence"],
        "filter_shot": filter_values["shot"],
        "filter_asset": filter_values["asset"],
        "filter_context": context_filter,
        "filters_active": filters_active,
    }

    return render(request, "core/artist_assignment.html", context)


def artist_info(request, artist_id):
    artist = get_object_or_404(Artist, pk=artist_id)
    if request.method == "POST":
        form = ArtistForm(request.POST, request.FILES, instance=artist)
        if form.is_valid():
            form.save()
            return redirect("artist_info", artist_id=artist.id)
    else:
        form = ArtistForm(instance=artist)

    return render(
        request,
        "core/artist_info.html",
        {
            "artist": artist,
            "form": form,
        },
    )


def update_task(request, task_id):
    """Update task attributes (status, type, description) while preserving open artists."""
    task = get_object_or_404(Task, pk=task_id)
    filters = _extract_filters(request.POST, prefix="filter_")
    if request.method == "POST":
        form = TaskUpdateForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            open_artists = request.POST.get("open_artists", "")
            return _redirect_with_state(filters, open_artists)
    return _redirect_with_state(filters)


def delete_task(request, task_id):
    """Deletes a Task and preserves open artists."""
    task = get_object_or_404(Task, pk=task_id)
    filters = _extract_filters(request.POST, prefix="filter_")
    if request.method == "POST":
        open_artists = request.POST.get("open_artists", "")
        task.delete()
        return _redirect_with_state(filters, open_artists)
    return _redirect_with_state(filters)
