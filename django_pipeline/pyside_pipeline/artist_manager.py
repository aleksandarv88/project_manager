import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import re

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
try:
    from pipe_common import env_vars as EV  # centralized env var keys
except Exception:
    EV = None  # fallback if package not available

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:  # Optional helper for version/iteration labels
    from pipeline_scripts import versioning  # type: ignore
except Exception:  # noqa: BLE001 - fallback if scripts unavailable
    versioning = None


PIPELINE_ROOT = BASE_DIR / 'pipeline_scripts'
PIPELINE_HOUDINI_DIR = PIPELINE_ROOT / 'houdini'
PIPELINE_MAYA_DIR = PIPELINE_ROOT / 'maya'
PIPELINE_LIBS_DIR = PIPELINE_ROOT / 'libs'
PIPELINE_HOUDINI_PYTHON_LIB = PIPELINE_LIBS_DIR / 'python311'
PIPELINE_MAYA_PYTHON_LIB = PIPELINE_LIBS_DIR / 'python39'


def _collect_python_paths() -> List[str]:
    paths: List[str] = []
    for entry in sys.path:
        if not entry:
            continue
        try:
            candidate = Path(entry)
        except TypeError:
            continue
        if not candidate.exists():
            continue
        lowered_parts = {part.lower() for part in candidate.parts}
        if 'site-packages' in lowered_parts or 'dist-packages' in lowered_parts:
            paths.append(str(candidate))
    return paths


def _unique_paths(paths: List[str]) -> List[str]:
    seen: set[str] = set()
    unique: List[str] = []
    for value in paths:
        if not value:
            continue
        normalized = '&' if value == '&' else os.path.normcase(os.path.normpath(value))
        if normalized not in seen:
            unique.append(value)
            seen.add(normalized)
    return unique


def _merge_path_list(new_entries: List[str], existing: Optional[str], separator: str) -> str:
    items = [entry for entry in new_entries if entry]
    if existing:
        items.extend([entry for entry in existing.split(separator) if entry])
    return separator.join(_unique_paths(items))


def _merge_python_paths(new_entries: List[str], existing: Optional[str]) -> str:
    items: List[str] = []
    items.extend(entry for entry in new_entries if entry)
    if existing:
        items.extend(entry for entry in existing.split(os.pathsep) if entry)
    return os.pathsep.join(_unique_paths(items))


def _build_houdini_path(existing: Optional[str]) -> str:
    new_entries = [str(PIPELINE_HOUDINI_DIR)]
    existing_entries: List[str] = []
    ampersand_present = False
    if existing:
        for part in existing.split(';'):
            part = part.strip()
            if not part:
                continue
            if part == '&':
                ampersand_present = True
            else:
                existing_entries.append(part)
    merged = _unique_paths(new_entries + existing_entries)
    if not ampersand_present:
        merged.append('&')
    return ';'.join(merged)


RUNTIME_SITE_PACKAGES = _collect_python_paths()

DEFAULT_DB_CONFIG: Dict[str, str] = {
    "dbname": "FX3X",
    "user": "postgres",
    "password": "Ifmatoodlon@321",
    "host": "localhost",
    "port": "5432",
}


def _parse_houdini_version(path: Path) -> tuple:
    match = re.search(r"Houdini\s+(\d+(?:\.\d+)*)", str(path))
    if not match:
        return (0,)
    parts: List[int] = []
    for token in match.group(1).split("."):
        try:
            parts.append(int(token))
        except ValueError:
            parts.append(0)
    return tuple(parts) if parts else (0,)


def _resolve_houdini_executable() -> Path:
    override = os.environ.get("PIPELINE_HOUDINI_EXE", "").strip()
    if override:
        return Path(override)

    root = Path(r"C:\Program Files\Side Effects Software")
    candidates = list(root.glob("Houdini */bin/houdini.exe"))
    if candidates:
        candidates.sort(key=_parse_houdini_version, reverse=True)
        return candidates[0]

    return Path(r"C:\\Program Files\\Side Effects Software\\Houdini 21.0.440\\bin\\houdini.exe")


SOFTWARE_EXECUTABLES: Dict[str, Path] = {
    "houdini": _resolve_houdini_executable(),
    "maya": Path(r"C:\\Program Files\\Autodesk\\Maya2023\\bin\\maya.exe"),
}

SOFTWARE_DISPLAY_NAMES: Dict[str, str] = {
    "houdini": "Houdini",
    "maya": "Maya",
}

STATUS_LABELS: Dict[str, str] = {
    "not_started": "Not Started",
    "wip": "Work In Progress",
    "internal_approved": "Approved Internally",
    "client_approved": "Approved by Client",
    "done": "Done",
}

DEPARTMENT_KEYWORDS: Dict[str, List[str]] = {
    "fx": ["fx", "effect", "sim"],
    "mod": ["model", "mod", "sculpt"],
    "layout": ["layout", "previz", "previs"],
    "anim": ["anim", "animation"],
    "lgt": ["light", "lighting", "lgt"],
    "cfx": ["cfx", "fur", "groom"],
    "ldev": ["look", "ldev", "shade", "texture"],
    "env": ["env", "environment"],
}

DEPARTMENT_SOFTWARE_MAP: Dict[str, List[str]] = {
    "fx": ["houdini", "maya"],
    "mod": ["maya", "houdini"],
    "layout": ["maya", "houdini"],
    "anim": ["maya"],
    "lgt": ["houdini", "maya"],
    "cfx": ["houdini", "maya"],
    "ldev": ["maya"],
    "env": ["houdini", "maya"],
}

DEFAULT_SOFTWARES: List[str] = ["houdini", "maya"]

SCENE_TABLE_NAME = os.environ.get("PIPELINE_SCENE_TABLE", "core_scene_file")

TASK_COLUMNS = [
    "ID",
    "Task",
    "Department",
    "Project",
    "Sequence",
    "Shot",
    "Asset",
    "Status",
]

SCENE_COLUMNS = ["Version", "Iteration", "Filename", "Updated"]


def _sanitize_folder_name(value: str, fallback: str) -> str:
    candidate = str(value or "").strip()
    if not candidate:
        candidate = fallback
    sanitized_chars = [
        ch if ch.isalnum() or ch in {"_", "-", "."} else "_"
        for ch in candidate
    ]
    sanitized = ''.join(sanitized_chars).strip('_').lower()
    if not sanitized:
        sanitized = fallback
    return sanitized


@dataclass
class TaskRecord:
    id: int
    artist_id: int
    artist_name: str
    task_name: str
    task_type: str
    status: str
    description: str
    asset_id: Optional[int]
    asset_name: str
    asset_type: str
    sequence_id: Optional[int]
    sequence_name: str
    shot_id: Optional[int]
    shot_name: str
    project_name: str
    project_base_path: str
    project_id: Optional[int]
    department: str
    context: str  # asset | shot | sequence | task

    def status_label(self) -> str:
        return STATUS_LABELS.get(self.status, self.status.replace("_", " ").title())

    def project_path(self) -> Optional[Path]:
        if not self.project_base_path or not self.project_name:
            return None
        return Path(self.project_base_path) / self.project_name

    def artist_folder_name(self) -> str:
        fallback = f"artist_{self.artist_id}"
        return _sanitize_folder_name(self.artist_name, fallback)

    def task_folder_name(self) -> str:
        if self.context == 'asset':
            return ''
        fallback = f"task_{self.id}"
        base = (self.task_name or '').strip() or (self.department or '').strip() or self.task_type
        return _sanitize_folder_name(base, fallback)

    def display_task_name(self) -> str:
        value = (self.task_name or '').strip()
        return value if value else (self.department or self.task_type).title()

    def scene_root(self) -> Optional[Path]:
        project_path = self.project_path()
        if not project_path:
            return None
        department = self.department or "fx"
        if self.context == "asset" and self.asset_name and self.asset_type:
            return project_path / "assets" / self.asset_type / self.asset_name / department
        if self.context == "shot" and self.sequence_name and self.shot_name:
            return project_path / "sequences" / self.sequence_name / self.shot_name / department
        if self.context == "sequence" and self.sequence_name:
            return project_path / "sequences" / self.sequence_name / department
        return project_path / "tasks" / f"task_{self.id}" / department

    def scene_dir_for(self, software: str) -> Optional[Path]:
        root = self.scene_root()
        software_key = (software or "").strip().lower()
        if not root or not software_key:
            return None
        return root / software_key / "scenes" / self.artist_folder_name() / self.task_folder_name()

    def ensure_workspace_dir(self, software: str) -> Optional[Path]:
        workspace = self.scene_dir_for(software)
        if not workspace:
            return None
        workspace.mkdir(parents=True, exist_ok=True)
        usd_dir = workspace / "usd"
        usd_dir.mkdir(parents=True, exist_ok=True)
        if self.asset_name:
            (usd_dir / self.asset_name).mkdir(parents=True, exist_ok=True)
        return workspace


@dataclass
class SceneRecord:
    id: int
    file_path: Path
    version: int
    iteration: int
    software: str
    artist_id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    def version_label(self) -> str:
        if versioning:
            return versioning.format_version_label(self.version)
        return f"v{int(self.version):03d}"

    def iteration_label(self) -> str:
        if versioning:
            return versioning.format_iteration_label(self.iteration)
        return f"i{int(self.iteration):03d}"

def build_db_params() -> Dict[str, str]:
    params: Dict[str, str] = {}
    params["dbname"] = os.environ.get("PIPELINE_DB_NAME", DEFAULT_DB_CONFIG["dbname"])
    params["user"] = os.environ.get("PIPELINE_DB_USER", DEFAULT_DB_CONFIG["user"])
    params["password"] = os.environ.get("PIPELINE_DB_PASSWORD", DEFAULT_DB_CONFIG["password"])
    params["host"] = os.environ.get("PIPELINE_DB_HOST", DEFAULT_DB_CONFIG["host"])
    params["port"] = os.environ.get("PIPELINE_DB_PORT", DEFAULT_DB_CONFIG["port"])
    return params


def ensure_scene_table(conn: psycopg2.extensions.connection) -> None:
    ident = sql.Identifier(SCENE_TABLE_NAME)
    unique_name = sql.Identifier(f"{SCENE_TABLE_NAME}_uniq")
    task_idx_name = sql.Identifier(f"{SCENE_TABLE_NAME}_task_idx")
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL(
                """
                CREATE TABLE IF NOT EXISTS {table} (
                    id SERIAL PRIMARY KEY,
                    task_id INTEGER NOT NULL REFERENCES core_task(id) ON DELETE CASCADE,
                    artist_id INTEGER NOT NULL REFERENCES core_artist(id) ON DELETE CASCADE,
                    software VARCHAR(32) NOT NULL,
                    file_path TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    iteration INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
                );
                """
            ).format(table=ident)
        )
        cur.execute(
            sql.SQL(
                "ALTER TABLE {table} ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;"
            ).format(table=ident)
        )
        cur.execute(
            sql.SQL(
                "ALTER TABLE {table} ADD COLUMN IF NOT EXISTS iteration INTEGER NOT NULL DEFAULT 1;"
            ).format(table=ident)
        )
        cur.execute(
            sql.SQL(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS {unique_idx}
                ON {table} (task_id, software, version, iteration);
                """
            ).format(unique_idx=unique_name, table=ident)
        )
        cur.execute(
            sql.SQL(
                """
                CREATE INDEX IF NOT EXISTS {task_idx}
                ON {table} (task_id, software, version);
                """
            ).format(task_idx=task_idx_name, table=ident)
        )
    conn.commit()


def resolve_department(task_type: str) -> str:
    lowered = (task_type or "").lower()
    for department, keywords in DEPARTMENT_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return department
    return "fx"


def resolve_software_options(department: str) -> List[str]:
    return DEPARTMENT_SOFTWARE_MAP.get((department or "").lower(), DEFAULT_SOFTWARES)


def format_timestamp(value: Optional[datetime]) -> str:
    if not value:
        return ""
    return value.strftime("%Y-%m-%d %H:%M")

class FX3XManager(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FX3X Artist Manager")
        self.resize(2000, 1220)

        self.db_params = build_db_params()
        self.conn = self._connect_database()
        self.current_artist_id: Optional[int] = None
        self.current_tasks: List[TaskRecord] = []
        self.current_task: Optional[TaskRecord] = None
        self.scene_records: List[SceneRecord] = []

        self._build_ui()
        self.load_artists()

    # ---------- UI Construction ----------
    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(16)

        header = QLabel("FX3X Artist Manager")
        header.setObjectName("HeaderLabel")
        main_layout.addWidget(header)

        selector_layout = QHBoxLayout()
        selector_layout.setSpacing(12)
        selector_label = QLabel("Artist")
        selector_label.setObjectName("FieldLabel")
        selector_layout.addWidget(selector_label)
        self.artist_combo = QComboBox()
        self.artist_combo.currentIndexChanged.connect(self.on_artist_changed)
        selector_layout.addWidget(self.artist_combo, 1)

        self.refresh_artists_btn = QPushButton("Refresh")
        self.refresh_artists_btn.setToolTip("Reload artists and tasks from the database")
        self.refresh_artists_btn.clicked.connect(self.on_refresh_artists)
        selector_layout.addWidget(self.refresh_artists_btn)

        main_layout.addLayout(selector_layout)

        body_layout = QHBoxLayout()
        body_layout.setSpacing(16)
        main_layout.addLayout(body_layout, 1)

        tasks_frame = self._create_card()
        tasks_layout = QVBoxLayout(tasks_frame)
        tasks_layout.setSpacing(12)
        tasks_header = QLabel("Assignments")
        tasks_header.setObjectName("SectionLabel")
        tasks_layout.addWidget(tasks_header)
        self.tasks_table = QTableWidget(0, len(TASK_COLUMNS))
        self.tasks_table.setHorizontalHeaderLabels(TASK_COLUMNS)
        self.tasks_table.verticalHeader().setVisible(False)
        self.tasks_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tasks_table.setSelectionMode(QTableWidget.SingleSelection)
        self.tasks_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tasks_table.itemSelectionChanged.connect(self.on_task_selection_changed)
        header_view = self.tasks_table.horizontalHeader()
        header_view.setStretchLastSection(True)
        header_view.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for col in range(1, len(TASK_COLUMNS)):
            header_view.setSectionResizeMode(col, QHeaderView.Stretch)
        tasks_layout.addWidget(self.tasks_table, 1)
        body_layout.addWidget(tasks_frame, 3)

        details_frame = self._create_card()
        details_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        details_layout = QVBoxLayout(details_frame)
        details_layout.setSpacing(12)
        details_header = QLabel("Assignment Details")
        details_header.setObjectName("SectionLabel")
        details_layout.addWidget(details_header)
        self.details_grid = QGridLayout()
        self.details_grid.setHorizontalSpacing(8)
        self.details_grid.setVerticalSpacing(6)
        self.details_grid.setColumnStretch(1, 1)
        details_layout.addLayout(self.details_grid)
        details_layout.addStretch(1)
        body_layout.addWidget(details_frame, 2)

        scenes_frame = self._create_card()
        scenes_layout = QVBoxLayout(scenes_frame)
        scenes_layout.setSpacing(12)
        scenes_header = QLabel("Scenes")
        scenes_header.setObjectName("SectionLabel")
        scenes_layout.addWidget(scenes_header)

        software_row = QHBoxLayout()
        software_row.setSpacing(10)
        software_label = QLabel("Software")
        software_label.setObjectName("FieldLabel")
        software_row.addWidget(software_label)
        self.software_combo = QComboBox()
        self.software_combo.currentIndexChanged.connect(self.on_software_changed)
        software_row.addWidget(self.software_combo, 1)
        self.refresh_scenes_btn = QPushButton("Refresh")
        self.refresh_scenes_btn.clicked.connect(self.load_scenes)
        software_row.addWidget(self.refresh_scenes_btn)
        scenes_layout.addLayout(software_row)

        self.scenes_table = QTableWidget(0, len(SCENE_COLUMNS))
        self.scenes_table.setHorizontalHeaderLabels(SCENE_COLUMNS)
        self.scenes_table.verticalHeader().setVisible(False)
        self.scenes_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.scenes_table.setSelectionMode(QTableWidget.SingleSelection)
        self.scenes_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.scenes_table.itemSelectionChanged.connect(self._on_scene_selection)
        self.scenes_table.itemDoubleClicked.connect(lambda *_: self.launch_selected_scene())
        scenes_header_view = self.scenes_table.horizontalHeader()
        scenes_header_view.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        scenes_header_view.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        scenes_header_view.setSectionResizeMode(2, QHeaderView.Stretch)
        scenes_header_view.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        scenes_layout.addWidget(self.scenes_table, 1)

        button_row = QHBoxLayout()
        button_row.setSpacing(12)
        self.launch_blank_btn = QPushButton("Launch Blank Session")
        self.launch_blank_btn.clicked.connect(self.launch_blank_session)
        button_row.addWidget(self.launch_blank_btn)
        self.open_scene_btn = QPushButton("Open Selected Scene")
        self.open_scene_btn.clicked.connect(self.launch_selected_scene)
        button_row.addWidget(self.open_scene_btn)
        scenes_layout.addLayout(button_row)
        body_layout.addWidget(scenes_frame, 3)

        self._build_detail_rows()
        self.tasks_table.setColumnHidden(0, True)
        self._update_buttons_enabled()

    def _create_card(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("Card")
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFrameShadow(QFrame.Raised)
        return frame

    def _format_status_label(self, status: str) -> str:
        value = status or ""
        return STATUS_LABELS.get(value, value.replace("_", " ").title())

    def _build_detail_rows(self) -> None:
        fields = [
            ("project", "Project"),
            ("sequence", "Sequence"),
            ("shot", "Shot"),
            ("asset", "Asset"),
            ("asset_type", "Asset Type"),
            ("task_name", "Task Name"),
            ("department", "Department"),
            ("status", "Status"),
            ("description", "Description"),
        ]
        self.detail_rows: Dict[str, tuple[QLabel, QLabel]] = {}
        for row, (key, label_text) in enumerate(fields):
            label = QLabel(label_text)
            label.setObjectName("FieldLabel")
            value = QLabel("-")
            value.setWordWrap(True)
            value.setObjectName("DetailValue")
            self.details_grid.addWidget(label, row, 0, alignment=Qt.AlignTop)
            self.details_grid.addWidget(value, row, 1, alignment=Qt.AlignTop)
            self.detail_rows[key] = (label, value)

    # ---------- Data loading ----------
    def _connect_database(self) -> psycopg2.extensions.connection:
        try:
            conn = psycopg2.connect(**self.db_params)
            conn.autocommit = True
            ensure_scene_table(conn)
            return conn
        except Exception as exc:  # noqa: BLE001
            self._show_critical("Database Error", f"Failed to connect to PostgreSQL: {exc}")
            raise

    def query_dicts(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, object]]:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params or ())
            return list(cur.fetchall())

    def on_refresh_artists(self) -> None:
        selected_id = getattr(self, 'current_artist_id', None)
        self.load_artists(selected_id)

    def load_artists(self, selected_artist_id: Optional[int] = None) -> None:
        artists = self.query_dicts("SELECT id, username FROM core_artist ORDER BY username;")
        self.artist_combo.blockSignals(True)
        self.artist_combo.clear()
        index_to_select = None
        for idx, artist in enumerate(artists):
            artist_id = int(artist["id"])
            self.artist_combo.addItem(str(artist["username"]), artist_id)
            if selected_artist_id is not None and artist_id == selected_artist_id:
                index_to_select = idx
        self.artist_combo.blockSignals(False)
        if artists:
            if index_to_select is None:
                index_to_select = 0
            self.artist_combo.setCurrentIndex(index_to_select)
            self.on_artist_changed()
        else:
            self.current_artist_id = None
            self.current_tasks = []
            self.current_task = None
            self.scene_records = []
            self.tasks_table.setRowCount(0)
            self.software_combo.blockSignals(True)
            self.software_combo.clear()
            self.software_combo.blockSignals(False)
            self._populate_tasks_table()
            self._update_buttons_enabled()

    def on_artist_changed(self) -> None:
        self.load_tasks()

    def load_tasks(self) -> None:
        artist_id = self.artist_combo.currentData()
        self.current_artist_id = int(artist_id) if artist_id is not None else None
        self.current_tasks = []
        self.current_task = None
        self.scene_records = []
        self.scenes_table.setRowCount(0)
        self.software_combo.blockSignals(True)
        self.software_combo.clear()
        self.software_combo.blockSignals(False)
        if self.current_artist_id is None:
            self.tasks_table.setRowCount(0)
            self._update_buttons_enabled()
            return
        rows = self.query_dicts(
            """
            SELECT
                t.id,
                t.task_type,
                t.task_name,
                t.description,
                t.status,
                t.artist_id,
                artist.username AS artist_username,
                a.id AS asset_id,
                a.name AS asset_name,
                a.asset_type AS asset_type,
                ap.id AS asset_project_id,
                ap.name AS asset_project_name,
                ap.base_path AS asset_project_base_path,
                seq.id AS sequence_id,
                seq.name AS sequence_name,
                sp.id AS sequence_project_id,
                sp.name AS sequence_project_name,
                sp.base_path AS sequence_project_base_path,
                shot.id AS shot_id,
                shot.name AS shot_name,
                shseq.name AS shot_sequence_name,
                shproj.id AS shot_project_id,
                shproj.name AS shot_project_name,
                shproj.base_path AS shot_project_base_path
            FROM core_task t
            JOIN core_artist artist ON artist.id = t.artist_id
            LEFT JOIN core_asset a ON t.asset_id = a.id
            LEFT JOIN core_project ap ON a.project_id = ap.id
            LEFT JOIN core_sequence seq ON t.sequence_id = seq.id
            LEFT JOIN core_project sp ON seq.project_id = sp.id
            LEFT JOIN core_shot shot ON t.shot_id = shot.id
            LEFT JOIN core_sequence shseq ON shot.sequence_id = shseq.id
            LEFT JOIN core_project shproj ON shot.project_id = shproj.id
            WHERE t.artist_id = %s
            ORDER BY t.id DESC;
            """,
            (self.current_artist_id,),
        )
        for row in rows:
            project_name = (
                row.get("shot_project_name")
                or row.get("asset_project_name")
                or row.get("sequence_project_name")
                or ""
            )
            project_base_path = (
                row.get("shot_project_base_path")
                or row.get("asset_project_base_path")
                or row.get("sequence_project_base_path")
                or ""
            )
            project_id_raw = (
                row.get("shot_project_id")
                or row.get("asset_project_id")
                or row.get("sequence_project_id")
            )
            has_asset = row.get("asset_id") is not None
            has_shot = row.get("shot_id") is not None
            has_sequence = row.get("sequence_id") is not None or row.get("shot_sequence_name") is not None
            context = (
                "asset" if has_asset else "shot" if has_shot else "sequence" if has_sequence else "task"
            )
            sequence_name = row.get("shot_sequence_name") or row.get("sequence_name") or ""
            task = TaskRecord(
                id=int(row["id"]),
                artist_id=int(row["artist_id"]),
                artist_name=str(row.get("artist_username") or ""),
                task_name=str(row.get("task_name") or ""),
                task_type=str(row.get("task_type") or ""),
                status=str(row.get("status") or ""),
                description=str(row.get("description") or ""),
                asset_id=int(row["asset_id"]) if row.get("asset_id") is not None else None,
                asset_name=str(row.get("asset_name") or ""),
                asset_type=str(row.get("asset_type") or ""),
                sequence_id=int(row["sequence_id"]) if row.get("sequence_id") is not None else None,
                sequence_name=sequence_name,
                shot_id=int(row["shot_id"]) if row.get("shot_id") is not None else None,
                shot_name=str(row.get("shot_name") or ""),
                project_name=str(project_name),
                project_base_path=str(project_base_path),
                project_id=int(project_id_raw) if project_id_raw is not None else None,
                department=resolve_department(str(row.get("task_type") or "")),
                context=context,
            )
            self.current_tasks.append(task)
        self._populate_tasks_table()
        self._update_buttons_enabled()

    def _populate_tasks_table(self) -> None:
        self.tasks_table.setRowCount(0)
        for task in self.current_tasks:
            row = self.tasks_table.rowCount()
            self.tasks_table.insertRow(row)
            id_item = QTableWidgetItem(str(task.id))
            id_item.setData(Qt.UserRole, task.id)
            self.tasks_table.setItem(row, 0, id_item)
            self.tasks_table.setItem(row, 1, QTableWidgetItem(task.display_task_name()))
            department_label = (task.department or task.task_type or "").upper()
            self.tasks_table.setItem(row, 2, QTableWidgetItem(department_label))
            self.tasks_table.setItem(row, 3, QTableWidgetItem(task.project_name))
            self.tasks_table.setItem(row, 4, QTableWidgetItem(task.sequence_name))
            self.tasks_table.setItem(row, 5, QTableWidgetItem(task.shot_name))
            self.tasks_table.setItem(row, 6, QTableWidgetItem(task.asset_name))
            status_item = QTableWidgetItem(task.status_label())
            status_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.tasks_table.setItem(row, 7, status_item)
            status_combo = self._build_status_combo(task)
            self.tasks_table.setCellWidget(row, 7, status_combo)
        if self.current_tasks:
            self.tasks_table.selectRow(0)
        else:
            self.populate_task_details(None)

    def _build_status_combo(self, task: TaskRecord) -> QComboBox:
        combo = QComboBox()
        for status_key, label in STATUS_LABELS.items():
            combo.addItem(label, status_key)
        if combo.findData(task.status) == -1:
            combo.addItem(task.status_label(), task.status)
        self._set_combo_status(combo, task.status)
        combo.setProperty("task_id", task.id)
        combo.setProperty("previous_status", task.status)
        combo.currentIndexChanged.connect(lambda _=None, widget=combo: self.on_task_status_changed(widget))
        return combo

    def _set_combo_status(self, combo: QComboBox, status: str) -> None:
        previous_state = combo.blockSignals(True)
        index = combo.findData(status)
        if index >= 0:
            combo.setCurrentIndex(index)
        combo.blockSignals(previous_state)

    def on_task_status_changed(self, combo: QComboBox) -> None:
        task_id_value = combo.property("task_id")
        previous_status_value = combo.property("previous_status") or ""
        new_status_value = combo.currentData()
        if task_id_value is None or new_status_value is None:
            return
        task_id = int(task_id_value)
        new_status = str(new_status_value)
        previous_status = str(previous_status_value) if previous_status_value else ""
        if new_status == previous_status:
            return
        if not self._commit_task_status(task_id, new_status):
            self._set_combo_status(combo, previous_status)
            return
        combo.setProperty("previous_status", new_status)

    def _commit_task_status(self, task_id: int, status: str) -> bool:
        try:
            with self.conn.cursor() as cur:
                cur.execute("UPDATE core_task SET status = %s WHERE id = %s;", (status, task_id))
        except Exception as exc:  # noqa: BLE001
            self._show_critical("Database Error", f"Failed to update task status: {exc}")
            return False
        task = next((record for record in self.current_tasks if record.id == task_id), None)
        status_label = self._format_status_label(status)
        if task:
            task.status = status
            status_label = task.status_label()
        row = self._find_task_row(task_id)
        if row is not None:
            item = self.tasks_table.item(row, 7)
            if item:
                item.setText(status_label)
        if self.current_task and self.current_task.id == task_id:
            self.current_task.status = status
            self._set_detail_value("status", status_label, True)
        return True

    def _find_task_row(self, task_id: int) -> Optional[int]:
        for row in range(self.tasks_table.rowCount()):
            item = self.tasks_table.item(row, 0)
            if not item:
                continue
            value = item.data(Qt.UserRole)
            if value is not None and int(value) == task_id:
                return row
        return None

    def on_task_selection_changed(self) -> None:
        selected_rows = self.tasks_table.selectionModel().selectedRows()
        if not selected_rows:
            self.current_task = None
            self.populate_task_details(None)
            self.scene_records = []
            self.scenes_table.setRowCount(0)
            self.software_combo.blockSignals(True)
            self.software_combo.clear()
            self.software_combo.blockSignals(False)
            self._update_buttons_enabled()
            return
        row = selected_rows[0].row()
        task_id = int(self.tasks_table.item(row, 0).data(Qt.UserRole))
        self.current_task = next((task for task in self.current_tasks if task.id == task_id), None)
        self.populate_task_details(self.current_task)
        self.populate_software_options()
        self.load_scenes()
        self._update_buttons_enabled()

    def populate_task_details(self, task: Optional[TaskRecord]) -> None:
        if not task:
            for key, (label, value) in self.detail_rows.items():
                label.setVisible(key == "project")
                value.setVisible(key == "project")
                value.setText("-" if key == "project" else "")
            return
        self._set_detail_value("project", task.project_name or "-", True)
        if task.context == "shot":
            self._set_detail_value("sequence", task.sequence_name or "-", True)
            self._set_detail_value("shot", task.shot_name or "-", True)
            self._set_detail_value("asset", "", False)
            self._set_detail_value("asset_type", "", False)
        elif task.context == "asset":
            self._set_detail_value("asset", task.asset_name or "-", True)
            self._set_detail_value("asset_type", task.asset_type or "-", bool(task.asset_type))
            self._set_detail_value("sequence", "", False)
            self._set_detail_value("shot", "", False)
        elif task.context == "sequence":
            self._set_detail_value("sequence", task.sequence_name or "-", True)
            self._set_detail_value("shot", "", False)
            self._set_detail_value("asset", "", False)
            self._set_detail_value("asset_type", "", False)
        else:
            self._set_detail_value("sequence", "", False)
            self._set_detail_value("shot", "", False)
            self._set_detail_value("asset", "", False)
            self._set_detail_value("asset_type", "", False)
        self._set_detail_value("task_name", task.display_task_name(), True)
        department_text = (task.department or task.task_type or "").upper()
        self._set_detail_value("department", department_text if department_text else "-", True)
        self._set_detail_value("status", task.status_label(), True)
        self._set_detail_value("description", task.description.strip(), bool(task.description.strip()))

    def _set_detail_value(self, key: str, text: str, visible: bool) -> None:
        label, value = self.detail_rows[key]
        label.setVisible(visible)
        value.setVisible(visible)
        if visible:
            value.setText(text if text else "-")
        else:
            value.setText("")

    def populate_software_options(self) -> None:
        self.software_combo.blockSignals(True)
        self.software_combo.clear()
        if not self.current_task:
            self.software_combo.blockSignals(False)
            return
        options = resolve_software_options(self.current_task.department)
        seen = set()
        for option in options:
            normalized = option.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            label = SOFTWARE_DISPLAY_NAMES.get(normalized, normalized.title())
            self.software_combo.addItem(label, normalized)
        if self.software_combo.count() == 0:
            for fallback in DEFAULT_SOFTWARES:
                label = SOFTWARE_DISPLAY_NAMES.get(fallback, fallback.title())
                self.software_combo.addItem(label, fallback)
        self.software_combo.blockSignals(False)
        if self.software_combo.count() > 0:
            self.software_combo.setCurrentIndex(0)

    def on_software_changed(self) -> None:
        self.load_scenes()

    def load_scenes(self) -> None:
        self.scene_records = []
        self.scenes_table.setRowCount(0)
        self.open_scene_btn.setEnabled(False)
        if not self.current_task or self.software_combo.count() == 0:
            return
        software = self.software_combo.currentData()
        if not software:
            return
        rows: List[Dict[str, object]] = []

        # Legacy scene-table records.
        try:
            query = sql.SQL(
                """
                SELECT id, task_id, artist_id, software, file_path, version, iteration, created_at, updated_at
                FROM {table}
                WHERE task_id = %s AND software = %s AND artist_id = %s
                ORDER BY version DESC, iteration DESC, id DESC;
                """
            ).format(table=sql.Identifier(SCENE_TABLE_NAME))
            rows.extend(
                self.query_dicts(
                    query.as_string(self.conn),
                    (
                        self.current_task.id,
                        software,
                        self.current_task.artist_id,
                    ),
                )
            )
        except Exception:
            # Keep UI functional even when legacy table is absent/unavailable.
            pass

        # New publish-based records (scene component preferred, then USD publish paths).
        publish_rows = self.query_dicts(
            """
            SELECT
                p.id,
                p.task_id,
                COALESCE(p.created_by_id, 0) AS artist_id,
                p.software,
                pc.file_path AS file_path,
                COALESCE(p.source_version, 0) AS version,
                COALESCE(p.source_iteration, 0) AS iteration,
                p.published_at AS created_at,
                p.updated_at
            FROM core_publish p
            LEFT JOIN LATERAL (
                SELECT c.file_path
                FROM core_publishcomponent c
                WHERE c.publish_id = p.id
                  AND c.component_type = 'scene'
                ORDER BY c.id ASC
                LIMIT 1
            ) pc ON TRUE
            WHERE p.task_id = %s
              AND p.software = %s
              AND (p.created_by_id = %s OR p.created_by_id IS NULL)
              AND pc.file_path IS NOT NULL
            ORDER BY p.source_version DESC, p.source_iteration DESC, p.id DESC;
            """,
            (
                self.current_task.id,
                software,
                self.current_task.artist_id,
            ),
        )
        rows.extend(publish_rows)

        # Deduplicate by identity of scene entry.
        dedup: Dict[tuple, Dict[str, object]] = {}
        for row in rows:
            key = (
                int(row.get("version") or 0),
                int(row.get("iteration") or 0),
                str(row.get("software") or "").lower(),
                int(row.get("artist_id") or 0),
                str(row.get("file_path") or ""),
            )
            if not key[-1]:
                continue
            if key not in dedup:
                dedup[key] = row
        ordered_rows = sorted(
            dedup.values(),
            key=lambda row: (
                int(row.get("version") or 0),
                int(row.get("iteration") or 0),
                int(row.get("id") or 0),
            ),
            reverse=True,
        )
        for row in ordered_rows:
            record = SceneRecord(
                id=int(row["id"]),
                file_path=Path(str(row.get("file_path"))),
                version=int(row.get("version") or 0),
                iteration=int(row.get("iteration") or 0),
                software=str(row.get("software") or "").lower(),
                artist_id=int(row.get("artist_id") or 0),
                created_at=row.get("created_at"),
                updated_at=row.get("updated_at"),
            )
            self.scene_records.append(record)
        for record in self.scene_records:
            row_index = self.scenes_table.rowCount()
            self.scenes_table.insertRow(row_index)
            version_item = QTableWidgetItem(record.version_label())
            iteration_item = QTableWidgetItem(record.iteration_label())
            filename = record.file_path.name
            filename_item = QTableWidgetItem(filename)
            filename_item.setToolTip(str(record.file_path))
            updated_item = QTableWidgetItem(format_timestamp(record.updated_at) or "")
            version_item.setData(Qt.UserRole, record.id)
            self.scenes_table.setItem(row_index, 0, version_item)
            self.scenes_table.setItem(row_index, 1, iteration_item)
            self.scenes_table.setItem(row_index, 2, filename_item)
            self.scenes_table.setItem(row_index, 3, updated_item)
        self._update_buttons_enabled()

    def _on_scene_selection(self) -> None:
        self._update_buttons_enabled()

    def _update_buttons_enabled(self) -> None:
        has_task = self.current_task is not None
        has_software = self.software_combo.count() > 0
        self.launch_blank_btn.setEnabled(has_task and has_software)
        self.refresh_scenes_btn.setEnabled(has_task and has_software)
        selection = self.scenes_table.selectionModel().selectedRows() if has_task else []
        self.open_scene_btn.setEnabled(bool(selection))
    # ---------- Launch actions ----------
    def launch_blank_session(self) -> None:
        if not self.current_task:
            self._show_warning("No task selected", "Please choose a task before launching a session.")
            return
        software = (self.software_combo.currentData() or "").lower()
        if not software:
            self._show_warning("No software", "Select a software package first.")
            return
        try:
            scene_dir = self.current_task.ensure_workspace_dir(software)
        except OSError as exc:
            self._show_critical("Workspace error", f"Could not prepare workspace directory:\n{exc}")
            return
        if not scene_dir:
            self._show_warning("Missing directory", "Cannot determine scene directory for this task.")
            return
        executable = SOFTWARE_EXECUTABLES.get(software)
        if not executable or not executable.exists():
            self._show_warning(
                "Executable not found",
                f"The configured path for {software.title()} is invalid:\n{executable}",
            )
            return
        env = self._build_environment(self.current_task, software, scene_dir, None)
        try:
            working_dir = str(scene_dir) if software == 'houdini' else None
            subprocess.Popen([str(executable)], env=env, cwd=working_dir)  # noqa: S603
        except Exception as exc:  # noqa: BLE001
            self._show_critical("Launch failed", f"Could not start {software.title()}: {exc}")

    def launch_selected_scene(self) -> None:
        if not self.current_task:
            self._show_warning("No task selected", "Please choose a task before launching a scene.")
            return
        selection = self.scenes_table.selectionModel().selectedRows()
        if not selection:
            self._show_warning("No scene selected", "Pick a scene from the table first.")
            return
        software = (self.software_combo.currentData() or "").lower()
        record = self.scene_records[selection[0].row()]
        scene_path = record.file_path
        if not scene_path.exists():
            self._show_warning(
                "Missing file",
                f"The scene file could not be found on disk:\n{scene_path}",
            )
            return
        executable = SOFTWARE_EXECUTABLES.get(software)
        if not executable or not executable.exists():
            self._show_warning(
                "Executable not found",
                f"The configured path for {software.title()} is invalid:\n{executable}",
            )
            return
        scene_dir = scene_path.parent
        scene_dir.mkdir(parents=True, exist_ok=True)
        env = self._build_environment(self.current_task, software, scene_dir, record)
        command = [str(executable), str(scene_path)]
        try:
            working_dir = str(scene_dir) if software == 'houdini' else None
            subprocess.Popen(command, env=env, cwd=working_dir)  # noqa: S603
        except Exception as exc:  # noqa: BLE001
            self._show_critical("Launch failed", f"Could not open scene: {exc}")

    def _build_environment(
        self,
        task: TaskRecord,
        software: str,
        scene_dir: Path,
        scene_record: Optional[SceneRecord],
    ) -> Dict[str, str]:
        env = os.environ.copy()
        env["PIPELINE_SOFTWARE"] = software
        env["SOFTWARE"] = software
        if EV:
            env[EV.SOFTWARE] = software
        # Ensure API base is available to DCCs (falls back to localhost dev server)
        api_base = os.environ.get("PIPELINE_API_BASE") or os.environ.get("API_BASE_URL") or "http://127.0.0.1:8002"
        env.setdefault("PIPELINE_API_BASE", api_base)
        env.setdefault("PM_API_URL", f"{api_base.rstrip('/')}/api/publishes/")
        env["PIPELINE_TASK_ID"] = str(task.id)
        env["TASK_ID"] = str(task.id)
        env["PM_TASK_ID"] = str(task.id)
        if EV:
            env[EV.TASK_ID] = str(task.id)
        env["PIPELINE_ARTIST_ID"] = str(task.artist_id)
        env["ARTIST_ID"] = str(task.artist_id)
        env["PM_ARTIST"] = task.artist_name or str(task.artist_id)
        if EV:
            env[EV.ARTIST_ID] = str(task.artist_id)
        if task.artist_name:
            env["PIPELINE_ARTIST_NAME"] = task.artist_name
            env["ARTIST_NAME"] = task.artist_name
            # Shorthand expected by some tools/scripts
            env["PIPELINE_ARTIST"] = task.artist_name
        if task.department:
            env["PIPELINE_DEPARTMENT"] = task.department
            env["DEPARTMENT"] = task.department
        if task.project_name:
            env["PIPELINE_PROJECT"] = task.project_name
            env["PROJECT"] = task.project_name
            env["PM_PROJECT"] = task.project_name
            if EV:
                env[EV.PROJECT] = task.project_name
        project_path = task.project_path()
        if project_path:
            env["PIPELINE_PROJECT_PATH"] = str(project_path)
            env["PROJECT_PATH"] = str(project_path)
            # ROOT should be the parent directory that contains all projects
            base_root = Path(task.project_base_path) if task.project_base_path else project_path.parent
            env["PIPELINE_PROJECT_ROOT"] = str(base_root)
            env["PROJECT_ROOT"] = str(base_root)
        if task.project_id:
            env["PIPELINE_PROJECT_ID"] = str(task.project_id)
            env["PROJECT_ID"] = str(task.project_id)
        if task.context == "asset" and task.asset_name:
            env["PIPELINE_ASSET"] = task.asset_name
            env["ASSET"] = task.asset_name
            if EV:
                env[EV.ASSET] = task.asset_name
            if task.asset_id:
                env["PIPELINE_ASSET_ID"] = str(task.asset_id)
                env["ASSET_ID"] = str(task.asset_id)
            if task.asset_type:
                env["PIPELINE_ASSET_TYPE"] = task.asset_type
                env["ASSET_TYPE"] = task.asset_type
                if EV:
                    env[EV.ASSET_TYPE] = task.asset_type
        if task.sequence_name:
            env["PIPELINE_SEQUENCE"] = task.sequence_name
            env["SEQUENCE"] = task.sequence_name
            env["PM_SEQ"] = task.sequence_name
            if EV:
                env[EV.SEQUENCE] = task.sequence_name
            if task.sequence_id:
                env["PIPELINE_SEQUENCE_ID"] = str(task.sequence_id)
                env["SEQUENCE_ID"] = str(task.sequence_id)
        if task.context == "shot" and task.shot_name:
            env["PIPELINE_SHOT"] = task.shot_name
            env["SHOT"] = task.shot_name
            env["PM_SHOT"] = task.shot_name
            if EV:
                env[EV.SHOT] = task.shot_name
            if task.shot_id:
                env["PIPELINE_SHOT_ID"] = str(task.shot_id)
                env["SHOT_ID"] = str(task.shot_id)
            # Provide shot root directory (<project>/sequences/<seq>/<shot>)
            if project_path and task.sequence_name:
                shot_root = project_path / "sequences" / task.sequence_name / task.shot_name
                env["PIPELINE_SHOT_ROOT"] = str(shot_root)
                env["SHOT_ROOT"] = str(shot_root)
        task_label = task.display_task_name()
        if task_label:
            env["PIPELINE_TASK_NAME"] = task_label
            env["TASK_NAME"] = task_label
        env["PIPELINE_TASK_FOLDER"] = task.task_folder_name()
        env["TASK_FOLDER"] = task.task_folder_name()
        env["PIPELINE_SCENE_DIR"] = str(scene_dir)
        env["SCENE_DIR"] = str(scene_dir)
        # DB variables (both legacy and short)
        env["PIPELINE_DB_NAME"] = self.db_params["dbname"]
        env["DB_NAME"] = self.db_params["dbname"]
        env["PIPELINE_DB_USER"] = self.db_params["user"]
        env["DB_USER"] = self.db_params["user"]
        env["PIPELINE_DB_PASSWORD"] = self.db_params["password"]
        env["DB_PASSWORD"] = self.db_params["password"]
        env["PIPELINE_DB_HOST"] = self.db_params["host"]
        env["DB_HOST"] = self.db_params["host"]
        env["PIPELINE_DB_PORT"] = self.db_params["port"]
        env["DB_PORT"] = self.db_params["port"]
        env["PIPELINE_SCENE_TABLE"] = SCENE_TABLE_NAME
        env["SCENE_TABLE"] = SCENE_TABLE_NAME
        env["PIPELINE_TOOLKIT_PATH"] = str(BASE_DIR)
        env["TOOLKIT_PATH"] = str(BASE_DIR)
        env["PIPELINE_SCRIPTS_PATH"] = str(PIPELINE_ROOT)
        env["SCRIPTS_PATH"] = str(PIPELINE_ROOT)
        if PIPELINE_HOUDINI_PYTHON_LIB.exists():
            env["PIPELINE_HOUDINI_PYTHON_LIB"] = str(PIPELINE_HOUDINI_PYTHON_LIB)
            env["HOUDINI_PYTHON_LIB"] = str(PIPELINE_HOUDINI_PYTHON_LIB)
        if PIPELINE_MAYA_PYTHON_LIB.exists():
            env["PIPELINE_MAYA_PYTHON_LIB"] = str(PIPELINE_MAYA_PYTHON_LIB)
            env["MAYA_PYTHON_LIB"] = str(PIPELINE_MAYA_PYTHON_LIB)
        if software == 'houdini':
            python_paths = [
                str(PIPELINE_HOUDINI_PYTHON_LIB),
                str(BASE_DIR),
                str(PIPELINE_ROOT),
            ]
            env["PYTHONPATH"] = _merge_python_paths(python_paths, env.get("PYTHONPATH"))
        elif software not in {'maya'}:
            python_paths = [str(BASE_DIR), str(PIPELINE_ROOT)]
            env["PYTHONPATH"] = _merge_python_paths(python_paths, env.get("PYTHONPATH"))
        if software == "houdini":
            env["HOUDINI_PATH"] = _build_houdini_path(env.get("HOUDINI_PATH"))
        elif software == "maya":
            env["MAYA_SCRIPT_PATH"] = _merge_path_list(
                [str(PIPELINE_ROOT)],
                env.get("MAYA_SCRIPT_PATH"),
                os.pathsep,
            )
        if scene_record:
            env["PIPELINE_SCENE_ID"] = str(scene_record.id)
            env["SCENE_ID"] = str(scene_record.id)
            env["PIPELINE_SCENE_PATH"] = str(scene_record.file_path)
            env["SCENE_PATH"] = str(scene_record.file_path)
            env["PIPELINE_SCENE_VERSION"] = str(scene_record.version)
            env["SCENE_VERSION"] = str(scene_record.version)
            env["PIPELINE_SCENE_ITERATION"] = str(scene_record.iteration)
            env["SCENE_ITERATION"] = str(scene_record.iteration)
        if software == "houdini" and scene_dir:
            env["HIP"] = str(scene_dir)
        elif software == "maya":
            if scene_dir:
                env["MAYA_PROJECT"] = str(scene_dir)
            elif project_path:
                env["MAYA_PROJECT"] = str(project_path)
        return env

    # ---------- Messaging ----------
    def _show_warning(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)

    def _show_critical(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)

    # ---------- Qt events ----------
    def closeEvent(self, event) -> None:  # type: ignore[override]
        try:
            if hasattr(self, "conn") and self.conn:
                self.conn.close()
        finally:
            super().closeEvent(event)

def apply_stylesheet(app: QApplication) -> None:
    app.setStyleSheet(
        """
        QWidget {
            background-color: #1f1f22;
            color: #f0f0f0;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 12pt;
        }
        #HeaderLabel {
            font-size: 24pt;
            font-weight: 600;
            color: #ff8800;
        }
        #SectionLabel {
            font-size: 14pt;
            font-weight: 600;
            margin-bottom: 4px;
        }
        #FieldLabel {
            font-weight: 600;
            color: #ffa64d;
        }
        #DetailValue {
            font-size: 11pt;
        }
        QFrame#Card {
            background-color: #2a2a2e;
            border-radius: 12px;
            border: 1px solid #3c3c42;
        }
        QComboBox {
            background-color: #343438;
            border: 1px solid #4c4c52;
            border-radius: 6px;
            padding: 6px 8px;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox QAbstractItemView {
            background-color: #2f2f33;
            color: #f6f6f6;
            selection-background-color: #ff8800;
            selection-color: #101010;
        }
        QTableWidget {
            background-color: #1f1f23;
            alternate-background-color: #26262a;
            gridline-color: #3e3e42;
            border: 1px solid #35353a;
            border-radius: 8px;
        }
        QHeaderView::section {
            background-color: #303035;
            color: #f0f0f0;
            padding: 6px;
            border: none;
        }
        QTableWidget::item:selected {
            background-color: #ff8800;
            color: #101010;
        }
        QPushButton {
            background-color: #ff8800;
            color: #101010;
            border: none;
            border-radius: 8px;
            padding: 8px 14px;
            font-weight: 600;
        }
        QPushButton:disabled {
            background-color: #3d3d42;
            color: #7a7a7f;
        }
        QPushButton:hover:!disabled {
            background-color: #ffa347;
        }
        QPushButton:pressed:!disabled {
            background-color: #cc6b00;
        }
        QMessageBox {
            background-color: #2a2a2e;
        }
        """
    )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(app)
    window = FX3XManager()
    window.show()
    sys.exit(app.exec_())

