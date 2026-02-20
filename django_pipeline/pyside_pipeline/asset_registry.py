from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

try:
    from PyQt5.QtCore import Qt  # type: ignore
    from PyQt5.QtGui import QDesktopServices  # type: ignore
    from PyQt5.QtWidgets import (  # type: ignore
        QApplication,
        QComboBox,
        QFileDialog,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QPlainTextEdit,
        QTabWidget,
        QTableWidget,
        QTableWidgetItem,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
except Exception:
    from PySide2.QtCore import Qt  # type: ignore
    from PySide2.QtGui import QDesktopServices  # type: ignore
    from PySide2.QtWidgets import (  # type: ignore
        QApplication,
        QComboBox,
        QFileDialog,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QPlainTextEdit,
        QTabWidget,
        QTableWidget,
        QTableWidgetItem,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )


def _setup_django() -> None:
    base_dir = Path(__file__).resolve().parents[1]  # django_pipeline
    project_dir = base_dir / "vfx_pipeline"
    if str(project_dir) not in sys.path:
        sys.path.insert(0, str(project_dir))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vfx_pipeline.settings")
    import django

    django.setup()


_setup_django()

from django.db import connections, transaction  # noqa: E402
from django.db.models import Max  # noqa: E402
from django.utils import timezone  # noqa: E402
from core.models import Asset, AssetTexture, AssetVersion, Project  # noqa: E402
try:
    from ui_style import apply_stylesheet
except Exception:
    try:
        from pyside_pipeline.ui_style import apply_stylesheet
    except Exception:
        def apply_stylesheet(app) -> None:
            pass


ASSET_NAME_RE = re.compile(r"^[A-Za-z0-9_]+$")
TEXTURE_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".tga", ".bmp", ".exr", ".hdr", ".tx"}


def _current_user() -> str:
    return (
        os.environ.get("PIPELINE_ARTIST")
        or os.environ.get("PIPELINE_ARTIST_NAME")
        or os.environ.get("USERNAME")
        or os.environ.get("USER")
        or "unknown"
    )


def _msg_error(parent: QWidget, message: str) -> None:
    QMessageBox.critical(parent, "Asset Registry", message)


def _msg_info(parent: QWidget, message: str) -> None:
    QMessageBox.information(parent, "Asset Registry", message)


@dataclass
class RegisterPayload:
    project: Project
    asset_name: str
    fbx_path: str
    textures_path: str
    asset_type: str
    asset_category: str
    skeleton_type: str
    pose_type: str
    deform_type: str
    units: str
    scale_to_canonical: float
    height_cm: Optional[int]
    gender: str
    age_group: str
    body_type: str
    role_tag: str
    role_text: str
    status: str
    notes: str
    qc_status: str
    qc_report_path: str


class RegisterTab(QWidget):
    def __init__(self, parent_window: "AssetRegistryWindow"):
        super().__init__()
        self.parent_window = parent_window
        self.valid_payload: Optional[RegisterPayload] = None
        self.last_registered_ref = ""
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        row = 0
        self.project_combo = QComboBox()
        self._reload_projects()
        form.addWidget(QLabel("project"), row, 0)
        form.addWidget(self.project_combo, row, 1)
        row += 1

        self.asset_name_edit = QLineEdit()
        form.addWidget(QLabel("asset_name *"), row, 0)
        form.addWidget(self.asset_name_edit, row, 1)
        row += 1

        self.fbx_path_edit = QLineEdit()
        self.fbx_path_edit.setReadOnly(True)
        self.fbx_name_display = QLineEdit()
        self.fbx_name_display.setReadOnly(True)
        self.textures_path_edit = QLineEdit()
        self.textures_path_edit.setReadOnly(True)
        load_fbx_btn = QPushButton("Load FBX...")
        load_fbx_btn.clicked.connect(self._pick_fbx)
        load_tex_btn = QPushButton("Load Textures Folder...")
        load_tex_btn.clicked.connect(self._pick_textures)
        fbx_row = QHBoxLayout()
        fbx_row.addWidget(self.fbx_path_edit)
        fbx_row.addWidget(load_fbx_btn)
        tex_row = QHBoxLayout()
        tex_row.addWidget(self.textures_path_edit)
        tex_row.addWidget(load_tex_btn)
        form.addWidget(QLabel("fbx_path *"), row, 0)
        form.addLayout(fbx_row, row, 1)
        row += 1
        form.addWidget(QLabel("fbx_name (from file)"), row, 0)
        form.addWidget(self.fbx_name_display, row, 1)
        row += 1
        form.addWidget(QLabel("textures_path *"), row, 0)
        form.addLayout(tex_row, row, 1)
        row += 1

        self.asset_type_combo = self._combo(("character", "Character"), ("prop", "Prop"))
        self.asset_type_combo.currentIndexChanged.connect(self._sync_character_fields)
        self.asset_category_combo = self._combo(
            ("human", "Human"),
            ("creature", "Creature"),
            ("robot", "Robot"),
            ("weapon", "Weapon"),
            ("bag", "Bag"),
            ("hair", "Hair"),
            ("other", "Other"),
        )
        self.skeleton_combo = self._combo(("mixamo", "Mixamo"), ("none", "None"), ("custom", "Custom"))
        self.pose_combo = self._combo(("t_pose", "T-Pose"), ("animation", "Animation"))
        self.deform_combo = self._combo(("skinned", "Skinned"), ("skeleton_only", "Skeleton Only"))
        self.units_combo = self._combo(("cm", "cm"), ("m", "m"))
        self.scale_edit = QLineEdit("1.0")
        self.height_edit = QLineEdit()

        form.addWidget(QLabel("asset_type *"), row, 0)
        form.addWidget(self.asset_type_combo, row, 1)
        row += 1
        form.addWidget(QLabel("asset_category *"), row, 0)
        form.addWidget(self.asset_category_combo, row, 1)
        row += 1
        form.addWidget(QLabel("skeleton_type *"), row, 0)
        form.addWidget(self.skeleton_combo, row, 1)
        row += 1
        form.addWidget(QLabel("pose_type *"), row, 0)
        form.addWidget(self.pose_combo, row, 1)
        row += 1
        form.addWidget(QLabel("deform_type *"), row, 0)
        form.addWidget(self.deform_combo, row, 1)
        row += 1
        form.addWidget(QLabel("units *"), row, 0)
        form.addWidget(self.units_combo, row, 1)
        row += 1
        form.addWidget(QLabel("scale_to_canonical *"), row, 0)
        form.addWidget(self.scale_edit, row, 1)
        row += 1
        self.height_label = QLabel("height_cm * (Character only)")
        form.addWidget(self.height_label, row, 0)
        form.addWidget(self.height_edit, row, 1)
        row += 1

        self.gender_combo = self._combo(
            ("male", "Male"), ("female", "Female"), ("neutral", "Neutral"), ("unknown", "Unknown")
        )
        self.age_group_combo = self._combo(
            ("child", "Child"), ("teen", "Teen"), ("adult", "Adult"), ("elder", "Elder"), ("unknown", "Unknown")
        )
        self.body_type_combo = self._combo(
            ("slim", "Slim"), ("average", "Average"), ("heavy", "Heavy"), ("athletic", "Athletic"), ("unknown", "Unknown")
        )
        self.role_tag_combo = self._combo(
            ("civilian", "Civilian"),
            ("soldier", "Soldier"),
            ("worker", "Worker"),
            ("police", "Police"),
            ("monster", "Monster"),
            ("custom", "Custom"),
        )
        self.role_tag_combo.currentIndexChanged.connect(self._sync_role_text)
        self.role_text_edit = QLineEdit()

        form.addWidget(QLabel("gender"), row, 0)
        form.addWidget(self.gender_combo, row, 1)
        row += 1
        form.addWidget(QLabel("age_group"), row, 0)
        form.addWidget(self.age_group_combo, row, 1)
        row += 1
        form.addWidget(QLabel("body_type"), row, 0)
        form.addWidget(self.body_type_combo, row, 1)
        row += 1
        self.role_text_label = QLabel("role_text (required when Custom)")
        form.addWidget(QLabel("role_tag"), row, 0)
        form.addWidget(self.role_tag_combo, row, 1)
        row += 1
        form.addWidget(self.role_text_label, row, 0)
        form.addWidget(self.role_text_edit, row, 1)
        row += 1

        self.status_combo = self._combo(("wip", "WIP"), ("approved", "Approved"))
        self.qc_status_combo = self._combo(("pending", "Pending"), ("pass", "Pass"), ("fail", "Fail"))
        self.qc_report_edit = QLineEdit()
        self.notes_edit = QPlainTextEdit()
        self.notes_edit.setFixedHeight(80)

        form.addWidget(QLabel("status *"), row, 0)
        form.addWidget(self.status_combo, row, 1)
        row += 1
        form.addWidget(QLabel("qc_status"), row, 0)
        form.addWidget(self.qc_status_combo, row, 1)
        row += 1
        form.addWidget(QLabel("qc_report_path"), row, 0)
        form.addWidget(self.qc_report_edit, row, 1)
        row += 1
        form.addWidget(QLabel("notes"), row, 0)
        form.addWidget(self.notes_edit, row, 1)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        self.validate_btn = QPushButton("Validate")
        self.validate_btn.clicked.connect(self._validate)
        self.register_btn = QPushButton("Register to DB")
        self.register_btn.setEnabled(False)
        self.register_btn.clicked.connect(self._register)
        self.copy_ref_btn = QPushButton("Copy Asset Ref")
        self.copy_ref_btn.setEnabled(False)
        self.copy_ref_btn.clicked.connect(self._copy_ref)
        btn_row.addWidget(self.validate_btn)
        btn_row.addWidget(self.register_btn)
        btn_row.addWidget(self.copy_ref_btn)
        layout.addLayout(btn_row)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setFixedHeight(120)
        layout.addWidget(self.result_text)

        self._sync_character_fields()
        self._sync_role_text()
        self._wire_dirty_events()

    def _wire_dirty_events(self) -> None:
        widgets = [
            self.project_combo,
            self.asset_name_edit,
            self.fbx_path_edit,
            self.textures_path_edit,
            self.asset_type_combo,
            self.asset_category_combo,
            self.skeleton_combo,
            self.pose_combo,
            self.deform_combo,
            self.units_combo,
            self.scale_edit,
            self.height_edit,
            self.gender_combo,
            self.age_group_combo,
            self.body_type_combo,
            self.role_tag_combo,
            self.role_text_edit,
            self.status_combo,
            self.qc_status_combo,
            self.qc_report_edit,
            self.notes_edit,
        ]
        for widget in widgets:
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(self._invalidate)
            elif isinstance(widget, QComboBox):
                widget.currentIndexChanged.connect(self._invalidate)
            elif isinstance(widget, QPlainTextEdit):
                widget.textChanged.connect(self._invalidate)

    def _invalidate(self) -> None:
        self.valid_payload = None
        self.register_btn.setEnabled(False)

    def _combo(self, *items: tuple[str, str]) -> QComboBox:
        combo = QComboBox()
        for value, label in items:
            combo.addItem(label, value)
        return combo

    def _reload_projects(self) -> None:
        current_project_id = self.project_combo.currentData()
        self.project_combo.clear()
        for project in Project.objects.order_by("name"):
            self.project_combo.addItem(project.name, project.id)
        if current_project_id is not None:
            idx = self.project_combo.findData(current_project_id)
            if idx >= 0:
                self.project_combo.setCurrentIndex(idx)

    def _pick_fbx(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select FBX", "", "FBX Files (*.fbx)")
        if path:
            self.fbx_path_edit.setText(path)
            self.fbx_name_display.setText(Path(path).name)
            self._invalidate()

    def _pick_textures(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Textures Folder")
        if path:
            self.textures_path_edit.setText(path)
            self._invalidate()

    def _sync_character_fields(self) -> None:
        is_character = self.asset_type_combo.currentData() == "character"
        for w in [
            self.gender_combo,
            self.age_group_combo,
            self.body_type_combo,
            self.role_tag_combo,
            self.role_text_edit,
            self.height_edit,
        ]:
            w.setEnabled(is_character)
        self.height_label.setEnabled(is_character)
        if not is_character:
            self.height_edit.clear()

    def _sync_role_text(self) -> None:
        custom = self.role_tag_combo.currentData() == "custom"
        self.role_text_edit.setEnabled(custom and self.asset_type_combo.currentData() == "character")
        self.role_text_label.setEnabled(custom and self.asset_type_combo.currentData() == "character")

    def _collect_payload(self) -> RegisterPayload:
        project_id = self.project_combo.currentData()
        project = Project.objects.filter(id=project_id).first()
        if project is None:
            raise ValueError("No project selected.")

        asset_type = self.asset_type_combo.currentData()
        is_character = asset_type == "character"
        height_cm = None
        if is_character:
            try:
                height_cm = int(self.height_edit.text().strip())
            except Exception:
                raise ValueError("height_cm is required for Character.")

        try:
            scale_to_canonical = float(self.scale_edit.text().strip())
        except Exception:
            raise ValueError("scale_to_canonical must be a number.")

        payload = RegisterPayload(
            project=project,
            asset_name=self.asset_name_edit.text().strip(),
            fbx_path=self.fbx_path_edit.text().strip(),
            textures_path=self.textures_path_edit.text().strip(),
            asset_type=asset_type,
            asset_category=self.asset_category_combo.currentData(),
            skeleton_type=self.skeleton_combo.currentData(),
            pose_type=self.pose_combo.currentData(),
            deform_type=self.deform_combo.currentData(),
            units=self.units_combo.currentData(),
            scale_to_canonical=scale_to_canonical,
            height_cm=height_cm,
            gender=self.gender_combo.currentData() if is_character else "",
            age_group=self.age_group_combo.currentData() if is_character else "",
            body_type=self.body_type_combo.currentData() if is_character else "",
            role_tag=self.role_tag_combo.currentData() if is_character else "",
            role_text=self.role_text_edit.text().strip() if is_character else "",
            status=self.status_combo.currentData(),
            notes=self.notes_edit.toPlainText().strip(),
            qc_status=self.qc_status_combo.currentData(),
            qc_report_path=self.qc_report_edit.text().strip(),
        )
        return payload

    def _validate(self) -> None:
        try:
            payload = self._collect_payload()
            if not payload.fbx_path or not payload.fbx_path.lower().endswith(".fbx") or not os.path.isfile(payload.fbx_path):
                raise ValueError("fbx_path must point to an existing .fbx file.")
            if payload.deform_type == "skinned":
                if not payload.textures_path or not os.path.isdir(payload.textures_path):
                    raise ValueError("textures_path must point to an existing directory for skinned assets.")
            if not ASSET_NAME_RE.match(payload.asset_name):
                raise ValueError("asset_name must match [A-Za-z0-9_]+")
            if payload.scale_to_canonical <= 0:
                raise ValueError("scale_to_canonical must be > 0")
            if payload.asset_type == "character":
                if payload.height_cm is None or payload.height_cm < 50 or payload.height_cm > 250:
                    raise ValueError("height_cm must be between 50 and 250 for Character.")
                if payload.role_tag == "custom" and not payload.role_text:
                    raise ValueError("role_text is required when role_tag is Custom.")
            self.valid_payload = payload
            self.register_btn.setEnabled(True)
            self.result_text.setPlainText("Validation passed.")
        except Exception as exc:
            self.valid_payload = None
            self.register_btn.setEnabled(False)
            _msg_error(self, str(exc))

    def _collect_texture_files(self, textures_path: str) -> List[dict]:
        if not textures_path:
            return []
        textures: List[dict] = []
        root = Path(textures_path)
        if not root.exists() or not root.is_dir():
            return []
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            ext = path.suffix.lower()
            if ext not in TEXTURE_EXTS:
                continue
            try:
                file_size = path.stat().st_size
            except OSError:
                file_size = None
            textures.append(
                {
                    "texture_name": path.name,
                    "texture_path": str(path.resolve()),
                    "file_ext": ext,
                    "file_size": file_size,
                }
            )
        return textures

    def _register(self) -> None:
        if self.valid_payload is None:
            _msg_error(self, "Run Validate first.")
            return

        payload = self.valid_payload
        with_name = Asset.objects.filter(name__iexact=payload.asset_name).order_by("id")
        if with_name.count() > 1:
            _msg_error(
                self,
                f"Multiple assets with name '{payload.asset_name}' already exist across projects. Resolve duplicates first.",
            )
            return
        asset = with_name.first()
        if asset is None:
            asset = Asset.objects.create(
                project=payload.project,
                name=payload.asset_name,
                code=payload.asset_name.lower(),
                asset_type="character" if payload.asset_type == "character" else "props",
                category=payload.asset_category,
                status="design",
            )

        texture_rows = self._collect_texture_files(payload.textures_path)
        fbx_name = Path(payload.fbx_path).name
        with transaction.atomic():
            next_version = (AssetVersion.objects.filter(asset=asset).aggregate(m=Max("version")).get("m") or 0) + 1
            version = AssetVersion.objects.create(
                asset=asset,
                version=next_version,
                fbx_name=fbx_name,
                fbx_path=payload.fbx_path,
                textures_path=payload.textures_path,
                asset_type=payload.asset_type,
                asset_category=payload.asset_category,
                skeleton_type=payload.skeleton_type,
                pose_type=payload.pose_type,
                deform_type=payload.deform_type,
                units=payload.units,
                scale_to_canonical=payload.scale_to_canonical,
                height_cm=payload.height_cm,
                gender=payload.gender,
                age_group=payload.age_group,
                body_type=payload.body_type,
                role_tag=payload.role_tag,
                role_text=payload.role_text,
                status=payload.status,
                notes=payload.notes,
                qc_status=payload.qc_status or "pending",
                qc_report_path=payload.qc_report_path,
                registered_by=_current_user(),
                registered_at=timezone.now(),
            )
            AssetTexture.objects.bulk_create(
                [
                    AssetTexture(
                        asset_version=version,
                        texture_name=item["texture_name"],
                        texture_path=item["texture_path"],
                        file_ext=item["file_ext"],
                        file_size=item["file_size"],
                    )
                    for item in texture_rows
                ]
            )

        self.last_registered_ref = f"asset:{asset.name}@v{version.version:03d}"
        self.copy_ref_btn.setEnabled(True)
        self.parent_window.library_tab.reload()
        self.parent_window.qc_tab.reload()
        self.result_text.setPlainText(
            "\n".join(
                [
                    f"Asset ID: {asset.id}",
                    f"Version: {version.version:03d}",
                    f"fbx_path: {version.fbx_path}",
                    f"textures_path: {version.textures_path}",
                    f"textures_registered: {len(texture_rows)}",
                    f"qc_status: {version.qc_status}",
                    f"ref: {self.last_registered_ref}",
                ]
            )
        )
        _msg_info(self, f"Registered {self.last_registered_ref}")

    def _copy_ref(self) -> None:
        if not self.last_registered_ref:
            return
        QApplication.clipboard().setText(self.last_registered_ref)


class LibraryTab(QWidget):
    def __init__(self, parent_window: Optional["AssetRegistryWindow"] = None):
        super().__init__()
        self.parent_window = parent_window
        self._build_ui()
        self.reload()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        filter_row = QGridLayout()

        self.search_edit = QLineEdit()
        self.asset_type_combo = self._combo(("", "All"), ("character", "Character"), ("prop", "Prop"))
        self.asset_category_combo = self._combo(
            ("", "All"),
            ("human", "Human"),
            ("creature", "Creature"),
            ("robot", "Robot"),
            ("weapon", "Weapon"),
            ("bag", "Bag"),
            ("hair", "Hair"),
            ("other", "Other"),
        )
        self.skeleton_combo = self._combo(("", "All"), ("mixamo", "Mixamo"), ("none", "None"), ("custom", "Custom"))
        self.pose_combo = self._combo(("", "All"), ("t_pose", "T-Pose"), ("animation", "Animation"))
        self.deform_combo = self._combo(("", "All"), ("skinned", "Skinned"), ("skeleton_only", "Skeleton Only"))
        self.status_combo = self._combo(("", "All"), ("wip", "WIP"), ("approved", "Approved"))
        self.qc_combo = self._combo(("", "All"), ("pending", "Pending"), ("pass", "Pass"), ("fail", "Fail"))
        self.role_combo = self._combo(
            ("", "All"),
            ("civilian", "Civilian"),
            ("soldier", "Soldier"),
            ("worker", "Worker"),
            ("police", "Police"),
            ("monster", "Monster"),
            ("custom", "Custom"),
        )
        filter_row.addWidget(QLabel("Search"), 0, 0)
        filter_row.addWidget(self.search_edit, 0, 1)
        filter_row.addWidget(QLabel("Type"), 0, 2)
        filter_row.addWidget(self.asset_type_combo, 0, 3)
        filter_row.addWidget(QLabel("Category"), 1, 0)
        filter_row.addWidget(self.asset_category_combo, 1, 1)
        filter_row.addWidget(QLabel("Skeleton"), 1, 2)
        filter_row.addWidget(self.skeleton_combo, 1, 3)
        filter_row.addWidget(QLabel("Status"), 2, 0)
        filter_row.addWidget(self.status_combo, 2, 1)
        filter_row.addWidget(QLabel("QC"), 2, 2)
        filter_row.addWidget(self.qc_combo, 2, 3)
        filter_row.addWidget(QLabel("Pose"), 3, 0)
        filter_row.addWidget(self.pose_combo, 3, 1)
        filter_row.addWidget(QLabel("Deform"), 3, 2)
        filter_row.addWidget(self.deform_combo, 3, 3)
        filter_row.addWidget(QLabel("Role"), 4, 0)
        filter_row.addWidget(self.role_combo, 4, 1)
        refresh_btn = QPushButton("Apply Filters")
        refresh_btn.clicked.connect(self.reload)
        filter_row.addWidget(refresh_btn, 4, 3)
        layout.addLayout(filter_row)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            [
                "asset_name",
                "asset_type/category",
                "version",
                "fbx_name",
                "pose/deform",
                "skeleton_type",
                "status",
                "qc_status",
                "registered_at/by",
            ]
        )
        self.table.itemSelectionChanged.connect(self._show_selected)
        layout.addWidget(self.table)

        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setFixedHeight(180)
        layout.addWidget(self.details)

        action_row = QHBoxLayout()
        self.open_fbx_btn = QPushButton("Open FBX location")
        self.open_fbx_btn.clicked.connect(self._open_fbx_location)
        self.open_tex_btn = QPushButton("Open textures folder")
        self.open_tex_btn.clicked.connect(self._open_textures_location)
        self.copy_ref_btn = QPushButton("Copy asset ref")
        self.copy_ref_btn.clicked.connect(self._copy_ref)
        self.copy_paths_btn = QPushButton("Copy paths")
        self.copy_paths_btn.clicked.connect(self._copy_paths)
        self.delete_btn = QPushButton("Delete selected version")
        self.delete_btn.clicked.connect(self._delete_selected_version)
        for btn in [self.open_fbx_btn, self.open_tex_btn, self.copy_ref_btn, self.copy_paths_btn, self.delete_btn]:
            action_row.addWidget(btn)
        layout.addLayout(action_row)

    def _combo(self, *items: tuple[str, str]) -> QComboBox:
        combo = QComboBox()
        for value, label in items:
            combo.addItem(label, value)
        return combo

    def _query(self):
        qs = AssetVersion.objects.select_related("asset").all()
        search = self.search_edit.text().strip()
        if search:
            qs = qs.filter(asset__name__icontains=search)
        for field, combo in [
            ("asset_type", self.asset_type_combo),
            ("asset_category", self.asset_category_combo),
            ("skeleton_type", self.skeleton_combo),
            ("pose_type", self.pose_combo),
            ("deform_type", self.deform_combo),
            ("status", self.status_combo),
            ("qc_status", self.qc_combo),
            ("role_tag", self.role_combo),
        ]:
            value = combo.currentData()
            if value:
                qs = qs.filter(**{field: value})
        return qs.order_by("-registered_at", "-version", "-id")

    def reload(self) -> None:
        rows = list(self._query()[:500])
        self.table.setRowCount(0)
        for row in rows:
            i = self.table.rowCount()
            self.table.insertRow(i)
            values = [
                row.asset.name,
                f"{row.get_asset_type_display()}/{row.get_asset_category_display()}",
                f"v{row.version:03d}",
                row.fbx_name,
                f"{row.get_pose_type_display()}/{row.get_deform_type_display()}",
                row.get_skeleton_type_display(),
                row.get_status_display(),
                row.get_qc_status_display(),
                f"{row.registered_at:%Y-%m-%d %H:%M} / {row.registered_by or '-'}",
            ]
            for j, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, row.id)
                self.table.setItem(i, j, item)
        self.details.clear()

    def _selected_version(self) -> Optional[AssetVersion]:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        version_id = rows[0].data(Qt.UserRole)
        return AssetVersion.objects.filter(id=version_id).select_related("asset").first()

    def _show_selected(self) -> None:
        version = self._selected_version()
        if not version:
            self.details.clear()
            return
        textures = list(version.textures.all())
        lines = [
            f"asset_name: {version.asset.name}",
            f"version: v{version.version:03d}",
            f"fbx_name: {version.fbx_name}",
            f"fbx_path: {version.fbx_path}",
            f"textures_path: {version.textures_path}",
            f"asset_type: {version.get_asset_type_display()}",
            f"asset_category: {version.get_asset_category_display()}",
            f"skeleton_type: {version.get_skeleton_type_display()}",
            f"pose_type: {version.get_pose_type_display()}",
            f"deform_type: {version.get_deform_type_display()}",
            f"units: {version.units}",
            f"scale_to_canonical: {version.scale_to_canonical}",
            f"height_cm: {version.height_cm if version.height_cm is not None else '-'}",
            f"gender/age/body: {version.gender or '-'} / {version.age_group or '-'} / {version.body_type or '-'}",
            f"role: {version.role_tag or '-'} ({version.role_text or '-'})",
            f"status: {version.status}",
            f"qc_status: {version.qc_status}",
            f"qc_report_path: {version.qc_report_path or '-'}",
            f"registered_by: {version.registered_by or '-'}",
            f"registered_at: {version.registered_at:%Y-%m-%d %H:%M}",
            f"textures: {len(textures)} files",
        ]
        if textures:
            lines.append("texture samples:")
            for item in textures[:10]:
                lines.append(f"- {item.texture_name} ({item.file_ext or '-'})")
        self.details.setPlainText("\n".join(lines))

    def _open_fbx_location(self) -> None:
        version = self._selected_version()
        if not version:
            return
        folder = Path(version.fbx_path).parent
        if folder.exists():
            QDesktopServices.openUrl(folder.as_uri())

    def _open_textures_location(self) -> None:
        version = self._selected_version()
        if not version:
            return
        folder = Path(version.textures_path)
        if folder.exists():
            QDesktopServices.openUrl(folder.as_uri())

    def _copy_ref(self) -> None:
        version = self._selected_version()
        if not version:
            return
        QApplication.clipboard().setText(f"asset:{version.asset.name}@v{version.version:03d}")

    def _copy_paths(self) -> None:
        version = self._selected_version()
        if not version:
            return
        QApplication.clipboard().setText(f"fbx_path={version.fbx_path}\ntextures_path={version.textures_path}")

    def _delete_selected_version(self) -> None:
        version = self._selected_version()
        if not version:
            _msg_error(self, "Select a version row first.")
            return
        reply = QMessageBox.question(
            self,
            "Delete Asset Version",
            f"Delete {version.asset.name} v{version.version:03d}?\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        version.delete()
        self.reload()
        if self.parent_window is not None:
            self.parent_window.qc_tab.reload()
        _msg_info(self, "Selected version deleted.")


class QCTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self.reload()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.summary = QTextEdit()
        self.summary.setReadOnly(True)
        self.summary.setFixedHeight(140)
        layout.addWidget(self.summary)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.reload)
        layout.addWidget(refresh_btn)

    def reload(self) -> None:
        pending = AssetVersion.objects.filter(qc_status="pending").count()
        passed = AssetVersion.objects.filter(qc_status="pass").count()
        failed = AssetVersion.objects.filter(qc_status="fail").count()
        recent_fail = AssetVersion.objects.filter(qc_status="fail").select_related("asset").order_by("-registered_at")[:10]
        lines = [f"Pending: {pending}", f"Pass: {passed}", f"Fail: {failed}", "", "Recent failures:"]
        for item in recent_fail:
            lines.append(f"- {item.asset.name} v{item.version:03d} ({item.registered_at:%Y-%m-%d})")
        self.summary.setPlainText("\n".join(lines))


class AssetRegistryWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Asset Registry & Library")
        self.resize(1200, 840)
        tabs = QTabWidget()
        self.register_tab = RegisterTab(self)
        self.library_tab = LibraryTab(self)
        self.qc_tab = QCTab()
        tabs.addTab(self.register_tab, "Register")
        tabs.addTab(self.library_tab, "Library")
        tabs.addTab(self.qc_tab, "QC / Reports")
        refresh_btn = QPushButton("Refresh DB")
        refresh_btn.clicked.connect(self._refresh_db)
        tabs.setCornerWidget(refresh_btn, Qt.TopRightCorner)
        self.setCentralWidget(tabs)

    def _refresh_db(self) -> None:
        # Force reconnect so long-running desktop session sees latest DB state.
        connections.close_all()
        self.register_tab._reload_projects()
        self.library_tab.reload()
        self.qc_tab.reload()
        _msg_info(self, "Database refreshed.")


def main() -> int:
    app = QApplication(sys.argv)
    apply_stylesheet(app)
    win = AssetRegistryWindow()
    win.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
