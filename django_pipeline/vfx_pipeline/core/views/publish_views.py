from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Optional

from django.shortcuts import render

from core.models import Project, Publish


@dataclass
class PublishRow:
    publish: Publish
    asset_name: str
    part_name: str
    preview_path: str


def _path_to_posix(value: str) -> str:
    return str(value or "").replace("\\", "/")


def _derive_asset_part(publish: Publish) -> tuple[str, str]:
    metadata = publish.metadata or {}
    asset_name = str(metadata.get("asset") or metadata.get("asset_name") or "").strip()
    part_name = str(metadata.get("fx_layer") or metadata.get("part_name") or "").strip()

    if asset_name and part_name:
        return asset_name, part_name

    path = _path_to_posix(publish.asset_usd_path or publish.item_usd_path or "")
    if not path:
        return asset_name or "unknown_asset", part_name or "unknown_part"

    # Expected convention: .../hou/usd/<asset>/<part>/<file>.usd
    parts = [p for p in PurePosixPath(path).parts if p not in {"/", ""}]
    if "usd" in parts:
        usd_idx = parts.index("usd")
        if not asset_name and len(parts) > usd_idx + 1:
            asset_name = parts[usd_idx + 1]
        if not part_name and len(parts) > usd_idx + 2:
            part_name = parts[usd_idx + 2]

    if not part_name:
        part_name = PurePosixPath(path).parent.name or "unknown_part"
    if not asset_name:
        asset_name = PurePosixPath(path).name.split("_")[0] or "unknown_asset"
    return asset_name, part_name


def _publish_rows(project_id: Optional[str] = None) -> list[PublishRow]:
    qs = Publish.objects.select_related("project", "task", "created_by").order_by("-published_at")
    if project_id:
        qs = qs.filter(project_id=project_id)
    # Focus page on Houdini/asset publishes.
    qs = qs.exclude(item_usd_path="").exclude(asset_usd_path="")

    rows: list[PublishRow] = []
    for publish in qs:
        asset_name, part_name = _derive_asset_part(publish)
        preview_path = publish.preview_path or ""
        rows.append(
            PublishRow(
                publish=publish,
                asset_name=asset_name,
                part_name=part_name,
                preview_path=preview_path,
            )
        )
    return rows


def publish_list_page(request):
    project_id = request.GET.get("project", "").strip()
    projects = Project.objects.order_by("name")
    rows = _publish_rows(project_id or None)

    latest_by_key: dict[tuple[str, str], PublishRow] = {}
    for row in rows:
        key = (row.asset_name, row.part_name)
        if key not in latest_by_key:
            latest_by_key[key] = row

    latest_rows = list(latest_by_key.values())
    context = {
        "projects": projects,
        "selected_project": project_id,
        "rows": latest_rows,
    }
    return render(request, "core/publish_list.html", context)


def publish_detail_page(request):
    asset_name = (request.GET.get("asset") or "").strip()
    part_name = (request.GET.get("part") or "").strip()
    project_id = (request.GET.get("project") or "").strip()

    rows = _publish_rows(project_id or None)
    rows = [row for row in rows if row.asset_name == asset_name and row.part_name == part_name]
    latest = rows[0] if rows else None

    context = {
        "asset_name": asset_name,
        "part_name": part_name,
        "project_id": project_id,
        "latest": latest,
        "history": rows,
    }
    return render(request, "core/publish_detail.html", context)
