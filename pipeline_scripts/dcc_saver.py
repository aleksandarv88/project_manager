from __future__ import annotations

import os
import re
import traceback
from pathlib import Path
from typing import Dict, Tuple

from . import db
from . import versioning

SAVE_EXTENSIONS = {
    "houdini": ".hip",
    "maya": ".mb",
}

SAVE_TYPES_MAYA = {
    ".ma": "mayaAscii",
    ".mb": "mayaBinary",
}


class PipelineContext(dict):
    @property
    def task_id(self) -> int:
        return int(self.get("task_id", 0))

    @property
    def artist_id(self) -> int:
        return int(self.get("artist_id", 0))

    @property
    def software(self) -> str:
        return (self.get("software") or "").lower()

    @property
    def scene_dir(self) -> Path:
        value = self.get("scene_dir") or ""
        return Path(value)

    @property
    def department(self) -> str:
        return (self.get("department") or "").strip()

    @property
    def asset(self) -> str:
        return (self.get("asset") or "").strip()

    @property
    def sequence(self) -> str:
        return (self.get("sequence") or "").strip()

    @property
    def shot(self) -> str:
        return (self.get("shot") or "").strip()

    @property
    def project(self) -> str:
        return (self.get("project") or "").strip()

    @property
    def artist_name(self) -> str:
        return (self.get("artist_name") or "").strip()

    @property
    def task_name(self) -> str:
        return (self.get("task_name") or "").strip()

    @property
    def task_folder(self) -> str:
        return (self.get("task_folder") or "").strip()


def save_new_version() -> None:
    _save_scene("version")


def save_new_iteration() -> None:
    _save_scene("iteration")


def _save_scene(bump: str) -> None:
    try:
        context = _collect_context()
    except ValueError as exc:
        _display_message(str(exc), level="error")
        return

    if context.software not in SAVE_EXTENSIONS:
        _display_message(
            f"Unsupported software for pipeline saving: {context.software}",
            level="error",
        )
        return

    try:
        with db.connection_from_env() as conn:
            version, iteration = versioning.next_numbers(
                conn,
                context.task_id,
                context.software,
                bump=bump,
            )
            file_path = _build_scene_path(context, version, iteration)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            _perform_save(context.software, file_path)
            versioning.record_scene(
                conn,
                context.task_id,
                context.artist_id,
                context.software,
                str(file_path),
                version,
                iteration,
            )
        os.environ["PIPELINE_SCENE_PATH"] = str(file_path)
        version_label = versioning.format_version_label(version)
        iteration_label = versioning.format_iteration_label(iteration)
        _display_message(
            f"Saved {file_path.name} ({version_label} {iteration_label})",
            level="info",
        )
    except Exception as exc:  # noqa: BLE001
        traceback.print_exc()
        _display_message(f"Pipeline save failed: {exc}", level="error")


def _collect_context() -> PipelineContext:
    required = {
        "PIPELINE_TASK_ID": "task_id",
        "PIPELINE_SOFTWARE": "software",
        "PIPELINE_SCENE_DIR": "scene_dir",
        "PIPELINE_ARTIST_ID": "artist_id",
    }
    data: Dict[str, str] = {}
    missing = []
    for env_key, alias in required.items():
        value = os.environ.get(env_key)
        if not value:
            missing.append(env_key)
        else:
            data[alias] = value
    if missing:
        raise ValueError(
            "Missing pipeline context variables: {}".format(", ".join(missing))
        )

    optional_keys = {
        "PIPELINE_DEPARTMENT": "department",
        "PIPELINE_ASSET": "asset",
        "PIPELINE_SEQUENCE": "sequence",
        "PIPELINE_SHOT": "shot",
        "PIPELINE_PROJECT": "project",
        "PIPELINE_TASK_NAME": "task_name",
        "PIPELINE_TASK_FOLDER": "task_folder",
        "PIPELINE_ARTIST_NAME": "artist_name",
    }
    for env_key, alias in optional_keys.items():
        value = os.environ.get(env_key)
        if value:
            data[alias] = value

    ctx = PipelineContext(data)
    if ctx.task_id <= 0:
        raise ValueError("Invalid pipeline task context")
    if not ctx.scene_dir:
        raise ValueError("Scene directory missing from pipeline context")
    return ctx


def _build_scene_path(context: PipelineContext, version: int, iteration: int) -> Path:
    extension = SAVE_EXTENSIONS.get(context.software, ".scene")
    parts: list[str] = []

    artist = context.artist_name or f"artist{context.artist_id}"
    parts.append(_sanitize_name(artist))

    department = context.department or ""
    if department:
        parts.append(_sanitize_name(department))

    if context.asset:
        parts.append(_sanitize_name(context.asset))
    else:
        task_label = context.task_name or context.task_folder
        if task_label:
            parts.append(_sanitize_name(task_label))
        if context.project:
            parts.append(_sanitize_name(context.project))
        if context.sequence:
            parts.append(_sanitize_name(context.sequence))
        if context.shot:
            parts.append(_sanitize_name(context.shot))
        if not (context.project or context.sequence or context.shot):
            parts.append(f"task{context.task_id}")

    base = _sanitize_name("_".join(filter(None, parts)))
    version_label = versioning.format_version_label(version)
    filename = f"{base}_{version_label}{extension}"
    return context.scene_dir / filename


def _sanitize_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_\-]+", "_", value)
    return cleaned.strip("_") or "scene"


def _perform_save(software: str, file_path: Path) -> None:
    if software == "houdini":
        import hou

        hou.hipFile.save(file_name=file_path.as_posix(), save_to_recent_files=True)
    elif software == "maya":
        import maya.cmds as cmds  # type: ignore

        target = file_path.as_posix()
        cmds.file(rename=target)
        extension = file_path.suffix.lower()
        file_type = SAVE_TYPES_MAYA.get(extension, "mayaBinary")
        cmds.file(save=True, type=file_type)
    else:
        raise ValueError(f"Unsupported software: {software}")


def _display_message(message: str, *, level: str = "info") -> None:
    software = (os.environ.get("PIPELINE_SOFTWARE") or "").lower()
    level = level.lower()
    if software == "houdini":
        import hou

        if level == "error":
            hou.ui.displayMessage(message, severity=hou.severityType.Error)
        else:
            severity = hou.severityType.ImportantMessage if level == "info" else hou.severityType.Message
            hou.ui.setStatusMessage(message, severity=severity)
    elif software == "maya":
        import maya.cmds as cmds  # type: ignore
        import maya.utils  # type: ignore

        if level == "error":
            cmds.confirmDialog(title="Pipeline", message=message, icon="critical")
        else:
            maya.utils.executeDeferred(lambda: cmds.inViewMessage(amg=message, pos="midCenter", fade=True))
    else:
        print(message)
