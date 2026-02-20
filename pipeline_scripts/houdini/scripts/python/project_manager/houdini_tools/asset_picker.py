from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import hou
try:
    from hutil.Qt import QtCore, QtWidgets
except Exception:
    try:
        from PySide2 import QtCore, QtWidgets
    except Exception:
        from PySide6 import QtCore, QtWidgets

try:
    from psycopg2.extras import RealDictCursor
except Exception as exc:  # pragma: no cover
    raise RuntimeError("psycopg2 is required for asset picker.") from exc

from pipeline_scripts.db import connection_from_env


TYPE_FILTERS = {"All": "", "Character": "character", "Prop": "prop"}
STATUS_FILTERS = {"All": "", "Approved": "approved", "WIP": "wip"}
SKELETON_FILTERS = {"All": "", "Mixamo": "mixamo", "None": "none", "Custom": "custom"}
DEFORM_FILTERS = {"All": "", "Skinned": "skinned", "Skeleton Only": "skeleton_only"}

KIND_KEYWORDS = {
    "diffuse": ["diffuse", "albedo", "basecolor", "base_color", "col", "color"],
    "specular": ["specular", "spec", "refl", "reflect"],
    "metallic": ["metallic", "metalness", "metal"],
    "normal": ["normal", "nrm", "nor"],
}


def _norm_path(value: Optional[str]) -> str:
    if not value:
        return ""
    return os.path.normpath(str(value)).replace("\\", "/")


def _exists(path: str) -> bool:
    return bool(path) and os.path.isfile(path)


def _asset_ref(asset_name: str, version: int) -> str:
    return f"asset:{asset_name}@v{int(version):03d}"


def _path_status(path: str) -> str:
    return "OK" if _exists(path) else "Missing"


def _classify_texture_kind(texture_name: str, texture_path: str) -> Optional[str]:
    text = f"{texture_name} {Path(texture_path).name}".lower()
    for kind in ("diffuse", "specular", "metallic", "normal"):
        for token in KIND_KEYWORDS[kind]:
            if token in text:
                return kind
    return None


class AssetPickerDB:
    def list_asset_versions(
        self,
        search: str = "",
        asset_type: str = "",
        status: str = "",
        skeleton_type: str = "",
        deform_type: str = "",
    ) -> List[Dict]:
        where: List[str] = []
        params: List[object] = []
        if search:
            where.append("(LOWER(a.name) LIKE %s OR LOWER(av.fbx_name) LIKE %s)")
            like = f"%{search.lower()}%"
            params.extend([like, like])
        if asset_type:
            where.append("av.asset_type = %s")
            params.append(asset_type)
        if status:
            where.append("av.status = %s")
            params.append(status)
        if skeleton_type:
            where.append("av.skeleton_type = %s")
            params.append(skeleton_type)
        if deform_type:
            where.append("av.deform_type = %s")
            params.append(deform_type)

        sql = """
            SELECT
                a.id AS asset_id,
                a.name AS asset_name,
                av.id AS asset_version_id,
                av.version,
                av.asset_type,
                av.status,
                av.skeleton_type,
                av.pose_type,
                av.deform_type,
                av.fbx_name,
                av.qc_status
            FROM core_assetversion av
            JOIN core_asset a ON a.id = av.asset_id
        """
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY LOWER(a.name), av.version DESC, av.id DESC"

        with connection_from_env() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                return [dict(row) for row in cur.fetchall()]

    def fetch_asset_version_detail(self, asset_version_id: int) -> Dict:
        sql_main = """
            SELECT
                a.id AS asset_id,
                a.name AS asset_name,
                av.id AS asset_version_id,
                av.version,
                av.fbx_name,
                av.fbx_path,
                av.deform_type
            FROM core_assetversion av
            JOIN core_asset a ON a.id = av.asset_id
            WHERE av.id = %s
        """
        sql_tex = """
            SELECT texture_name, texture_path
            FROM core_assettexture
            WHERE asset_version_id = %s
            ORDER BY id ASC
        """

        with connection_from_env() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql_main, [asset_version_id])
                row = cur.fetchone()
                if not row:
                    raise RuntimeError(f"Asset version {asset_version_id} not found.")
                result = dict(row)
                cur.execute(sql_tex, [asset_version_id])
                texture_rows = [dict(r) for r in cur.fetchall()]

        texture_map: Dict[str, str] = {}
        texture_list: List[Dict[str, str]] = []
        for tex in texture_rows:
            tex_name = str(tex.get("texture_name") or "")
            tex_path = _norm_path(str(tex.get("texture_path") or ""))
            if not tex_path:
                continue
            kind = _classify_texture_kind(tex_name, tex_path)
            if kind and kind not in texture_map:
                texture_map[kind] = tex_path
            texture_list.append({"kind": kind or "other", "name": tex_name, "path": tex_path})

        result["fbx_path"] = _norm_path(str(result.get("fbx_path") or ""))
        result["textures"] = texture_map
        result["texture_files"] = texture_list
        return result

    def list_animation_versions(
        self,
        search: str = "",
        asset_type: str = "",
        status: str = "",
        skeleton_type: str = "",
        deform_type: str = "",
    ) -> List[Dict]:
        where: List[str] = ["av.pose_type = 'animation'"]
        params: List[object] = []
        if search:
            where.append("(LOWER(a.name) LIKE %s OR LOWER(av.fbx_name) LIKE %s)")
            like = f"%{search.lower()}%"
            params.extend([like, like])
        if asset_type:
            where.append("av.asset_type = %s")
            params.append(asset_type)
        if status:
            where.append("av.status = %s")
            params.append(status)
        if skeleton_type:
            where.append("av.skeleton_type = %s")
            params.append(skeleton_type)
        if deform_type:
            where.append("av.deform_type = %s")
            params.append(deform_type)

        sql = """
            SELECT
                a.id AS asset_id,
                a.name AS asset_name,
                av.id AS asset_version_id,
                av.version,
                av.asset_type,
                av.status,
                av.skeleton_type,
                av.deform_type,
                av.fbx_name,
                av.fbx_path,
                av.qc_status
            FROM core_assetversion av
            JOIN core_asset a ON a.id = av.asset_id
            WHERE
        """
        sql += " AND ".join(where)
        sql += " ORDER BY LOWER(a.name), av.version DESC, av.id DESC"
        with connection_from_env() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                rows = [dict(row) for row in cur.fetchall()]
        for row in rows:
            row["fbx_path"] = _norm_path(row.get("fbx_path"))
        return rows


class AssetPickerDialog(QtWidgets.QDialog):
    def __init__(self, hda_node, parent=None):
        super().__init__(parent or hou.qt.mainWindow())
        self.setWindowTitle("Select Asset")
        self.resize(1080, 640)
        self._hda_node = hda_node
        self._db = AssetPickerDB()
        self._rows: List[Dict] = []
        self._selected_detail: Optional[Dict] = None
        self._build_ui()
        self._wire_events()
        self.refresh_list()

    def _build_ui(self) -> None:
        root = QtWidgets.QVBoxLayout(self)

        top = QtWidgets.QHBoxLayout()
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("Search asset_name or fbx_name")
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.addItems(list(TYPE_FILTERS.keys()))
        self.status_combo = QtWidgets.QComboBox()
        self.status_combo.addItems(list(STATUS_FILTERS.keys()))
        self.skeleton_combo = QtWidgets.QComboBox()
        self.skeleton_combo.addItems(list(SKELETON_FILTERS.keys()))
        self.deform_combo = QtWidgets.QComboBox()
        self.deform_combo.addItems(list(DEFORM_FILTERS.keys()))
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        top.addWidget(QtWidgets.QLabel("Search"))
        top.addWidget(self.search_edit, 1)
        top.addWidget(QtWidgets.QLabel("Type"))
        top.addWidget(self.type_combo)
        top.addWidget(QtWidgets.QLabel("Status"))
        top.addWidget(self.status_combo)
        top.addWidget(QtWidgets.QLabel("Skeleton"))
        top.addWidget(self.skeleton_combo)
        top.addWidget(QtWidgets.QLabel("Deform"))
        top.addWidget(self.deform_combo)
        top.addWidget(self.refresh_btn)
        root.addLayout(top)

        center = QtWidgets.QSplitter()
        center.setOrientation(QtCore.Qt.Horizontal)
        root.addWidget(center, 1)

        self.table = self._make_table()
        center.addWidget(self.table)

        detail_widget = QtWidgets.QWidget()
        detail_layout = QtWidgets.QFormLayout(detail_widget)
        self.asset_ref_label = QtWidgets.QLabel("-")
        self.fbx_path_label = QtWidgets.QLabel("-")
        self.diffuse_label = QtWidgets.QLabel("-")
        self.specular_label = QtWidgets.QLabel("-")
        self.metallic_label = QtWidgets.QLabel("-")
        self.normal_label = QtWidgets.QLabel("-")
        for lbl in (
            self.asset_ref_label,
            self.fbx_path_label,
            self.diffuse_label,
            self.specular_label,
            self.metallic_label,
            self.normal_label,
        ):
            lbl.setWordWrap(True)

        self.validation_label = QtWidgets.QLabel("")
        self.validation_label.setWordWrap(True)
        self.validation_label.setStyleSheet("color: #ff5555;")

        detail_layout.addRow("Asset Ref", self.asset_ref_label)
        detail_layout.addRow("FBX Path", self.fbx_path_label)
        detail_layout.addRow("Diffuse Path", self.diffuse_label)
        detail_layout.addRow("Specular Path", self.specular_label)
        detail_layout.addRow("Metallic Path", self.metallic_label)
        detail_layout.addRow("Normal Path", self.normal_label)
        detail_layout.addRow("Validation", self.validation_label)
        center.addWidget(detail_widget)
        center.setSizes([680, 400])

        btns = QtWidgets.QHBoxLayout()
        btns.addStretch(1)
        self.load_btn = QtWidgets.QPushButton("Load")
        self.load_btn.setEnabled(False)
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        btns.addWidget(self.load_btn)
        btns.addWidget(self.cancel_btn)
        root.addLayout(btns)

    def _make_table(self) -> QtWidgets.QTableWidget:
        table = QtWidgets.QTableWidget(0, 7)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        table.setHorizontalHeaderLabels(
            ["Asset Name", "Version", "Type", "Status", "Skeleton", "FBX Name", "QC"]
        )
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        return table

    def _wire_events(self) -> None:
        self.refresh_btn.clicked.connect(self.refresh_list)
        self.search_edit.textChanged.connect(self.refresh_list)
        self.type_combo.currentIndexChanged.connect(self.refresh_list)
        self.status_combo.currentIndexChanged.connect(self.refresh_list)
        self.skeleton_combo.currentIndexChanged.connect(self.refresh_list)
        self.deform_combo.currentIndexChanged.connect(self.refresh_list)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        self.load_btn.clicked.connect(self._on_load)
        self.cancel_btn.clicked.connect(self.reject)

    def refresh_list(self) -> None:
        try:
            self._rows = self._db.list_asset_versions(
                search=self.search_edit.text().strip(),
                asset_type=TYPE_FILTERS[self.type_combo.currentText()],
                status=STATUS_FILTERS[self.status_combo.currentText()],
                skeleton_type=SKELETON_FILTERS[self.skeleton_combo.currentText()],
                deform_type=DEFORM_FILTERS[self.deform_combo.currentText()],
            )
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Database Error", str(exc))
            return
        self.table.setRowCount(0)
        for row in self._rows:
            pose_type = str(row.get("pose_type") or "t_pose")
            if pose_type != "t_pose":
                continue
            r = self.table.rowCount()
            self.table.insertRow(r)
            values = [
                row.get("asset_name", ""),
                f"v{int(row.get('version') or 0):03d}",
                str(row.get("asset_type") or ""),
                str(row.get("status") or ""),
                str(row.get("skeleton_type") or ""),
                str(row.get("fbx_name") or ""),
                str(row.get("qc_status") or ""),
            ]
            for c, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(value)
                item.setData(QtCore.Qt.UserRole, row.get("asset_version_id"))
                self.table.setItem(r, c, item)
        self._selected_detail = None
        self._clear_detail()

    def _clear_detail(self) -> None:
        self.asset_ref_label.setText("-")
        self.fbx_path_label.setText("-")
        self.diffuse_label.setText("-")
        self.specular_label.setText("-")
        self.metallic_label.setText("-")
        self.normal_label.setText("-")
        self.validation_label.setText("")
        self.load_btn.setEnabled(False)

    def _set_path_label(self, label: QtWidgets.QLabel, path: str) -> None:
        status = _path_status(path)
        if path:
            label.setText(f"{path} [{status}]")
        else:
            label.setText(f"- [{status}]")

    def _on_row_selected(self) -> None:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            self._selected_detail = None
            self._clear_detail()
            return
        version_id = selected[0].data(QtCore.Qt.UserRole)
        if not version_id:
            return
        try:
            detail = self._db.fetch_asset_version_detail(int(version_id))
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Database Error", str(exc))
            self._selected_detail = None
            self._clear_detail()
            return
        self._selected_detail = detail
        texture_map = detail.get("textures", {}) or {}
        diffuse = _norm_path(texture_map.get("diffuse", ""))
        specular = _norm_path(texture_map.get("specular", ""))
        metallic = _norm_path(texture_map.get("metallic", ""))
        normal = _norm_path(texture_map.get("normal", ""))
        fbx_path = _norm_path(detail.get("fbx_path", ""))
        self.asset_ref_label.setText(_asset_ref(detail["asset_name"], detail["version"]))
        self._set_path_label(self.fbx_path_label, fbx_path)
        self._set_path_label(self.diffuse_label, diffuse)
        self._set_path_label(self.specular_label, specular)
        self._set_path_label(self.metallic_label, metallic)
        self._set_path_label(self.normal_label, normal)
        deform_type = str(detail.get("deform_type") or "skinned")
        is_valid, message = self._validate_paths(
            fbx_path, diffuse, specular, metallic, normal, deform_type
        )
        self.validation_label.setText(message)
        self.load_btn.setEnabled(is_valid)

    def _validate_paths(
        self,
        fbx_path: str,
        diffuse: str,
        specular: str,
        metallic: str,
        normal: str,
        deform_type: str,
    ) -> Tuple[bool, str]:
        errors: List[str] = []
        if not _exists(fbx_path):
            errors.append("FBX path missing or not found.")
        if deform_type != "skeleton_only":
            if not _exists(diffuse) or not _exists(specular):
                errors.append("Diffuse and Specular are required.")
            if metallic and not _exists(metallic):
                errors.append("Metallic path provided but file is missing.")
            if normal and not _exists(normal):
                errors.append("Normal path provided but file is missing.")
        if errors:
            return False, " ".join(errors)
        return True, "Ready to load."

    def _set_parm_if_exists(self, parm_name: str, value) -> None:
        parm = self._hda_node.parm(parm_name)
        if parm is not None:
            parm.set(value)

    def _on_load(self) -> None:
        detail = self._selected_detail
        if not detail:
            return
        texture_map = detail.get("textures", {}) or {}
        fbx_path = _norm_path(detail.get("fbx_path", ""))
        diffuse = _norm_path(texture_map.get("diffuse", ""))
        specular = _norm_path(texture_map.get("specular", ""))
        metallic = _norm_path(texture_map.get("metallic", ""))
        normal = _norm_path(texture_map.get("normal", ""))
        deform_type = str(detail.get("deform_type") or "skinned")
        is_valid, message = self._validate_paths(
            fbx_path, diffuse, specular, metallic, normal, deform_type
        )
        if not is_valid:
            QtWidgets.QMessageBox.warning(self, "Validation", message)
            return

        self._set_parm_if_exists("fbx_path", fbx_path)
        self._set_parm_if_exists("diffuse", diffuse or "")
        self._set_parm_if_exists("specular", specular or "")
        self._set_parm_if_exists("metalic", metallic or "")
        self._set_parm_if_exists("normal", normal or "")
        self._set_parm_if_exists("tex_diffuse", diffuse or "")
        self._set_parm_if_exists("tex_specular", specular or "")
        self._set_parm_if_exists("tex_metallic", metallic or "")
        self._set_parm_if_exists("tex_normal", normal or "")
        # OTL expects an asset path in `asset` parm.
        self._set_parm_if_exists("asset", fbx_path)
        # Optional readable label parm if present.
        self._set_parm_if_exists("asset_label", detail.get("asset_name", ""))
        self._set_parm_if_exists("agentname", detail.get("asset_name", ""))
        self._set_parm_if_exists("asset_version", int(detail.get("version") or 0))
        self._set_parm_if_exists("asset_ref", _asset_ref(detail["asset_name"], detail["version"]))
        self.accept()


def open_asset_picker(hda_node: hou.Node) -> Optional[Dict]:
    dialog = AssetPickerDialog(hda_node=hda_node, parent=hou.qt.mainWindow())
    result = dialog.exec_()
    if result != QtWidgets.QDialog.Accepted or not dialog._selected_detail:
        return None
    detail = dialog._selected_detail
    textures = detail.get("textures", {}) or {}
    return {
        "asset_name": detail.get("asset_name", ""),
        "version": int(detail.get("version") or 0),
        "asset_ref": _asset_ref(detail.get("asset_name", ""), int(detail.get("version") or 0)),
        "fbx_path": _norm_path(detail.get("fbx_path", "")),
        "textures": {k: _norm_path(v) for k, v in textures.items() if v},
        "texture_files": detail.get("texture_files", []),
    }


class AnimationPickerDialog(QtWidgets.QDialog):
    def __init__(self, hda_node, parent=None):
        super().__init__(parent or hou.qt.mainWindow())
        self.setWindowTitle("Select Animations")
        self.resize(980, 560)
        self._hda_node = hda_node
        self._db = AssetPickerDB()
        self._rows: List[Dict] = []
        self._build_ui()
        self._wire_events()
        self.refresh_list()

    def _build_ui(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        top = QtWidgets.QHBoxLayout()
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("Search asset_name or fbx_name")
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.addItems(list(TYPE_FILTERS.keys()))
        self.status_combo = QtWidgets.QComboBox()
        self.status_combo.addItems(list(STATUS_FILTERS.keys()))
        self.skeleton_combo = QtWidgets.QComboBox()
        self.skeleton_combo.addItems(list(SKELETON_FILTERS.keys()))
        self.deform_combo = QtWidgets.QComboBox()
        self.deform_combo.addItems(list(DEFORM_FILTERS.keys()))
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        top.addWidget(QtWidgets.QLabel("Search"))
        top.addWidget(self.search_edit, 1)
        top.addWidget(QtWidgets.QLabel("Type"))
        top.addWidget(self.type_combo)
        top.addWidget(QtWidgets.QLabel("Status"))
        top.addWidget(self.status_combo)
        top.addWidget(QtWidgets.QLabel("Skeleton"))
        top.addWidget(self.skeleton_combo)
        top.addWidget(QtWidgets.QLabel("Deform"))
        top.addWidget(self.deform_combo)
        top.addWidget(self.refresh_btn)
        root.addLayout(top)

        self.table = QtWidgets.QTableWidget(0, 8)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setHorizontalHeaderLabels(
            ["Asset Name", "Version", "Type", "Status", "Skeleton", "Deform", "FBX Name", "QC"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        root.addWidget(self.table, 1)

        self.info_label = QtWidgets.QLabel("Pick one or more animation clips.")
        self.info_label.setWordWrap(True)
        root.addWidget(self.info_label)

        btns = QtWidgets.QHBoxLayout()
        btns.addStretch(1)
        self.load_btn = QtWidgets.QPushButton("Load Animations")
        self.load_btn.setEnabled(False)
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        btns.addWidget(self.load_btn)
        btns.addWidget(self.cancel_btn)
        root.addLayout(btns)

    def _wire_events(self) -> None:
        self.refresh_btn.clicked.connect(self.refresh_list)
        self.search_edit.textChanged.connect(self.refresh_list)
        self.type_combo.currentIndexChanged.connect(self.refresh_list)
        self.status_combo.currentIndexChanged.connect(self.refresh_list)
        self.skeleton_combo.currentIndexChanged.connect(self.refresh_list)
        self.deform_combo.currentIndexChanged.connect(self.refresh_list)
        self.table.itemSelectionChanged.connect(self._update_selection_state)
        self.load_btn.clicked.connect(self._on_load)
        self.cancel_btn.clicked.connect(self.reject)

    def refresh_list(self) -> None:
        try:
            self._rows = self._db.list_animation_versions(
                search=self.search_edit.text().strip(),
                asset_type=TYPE_FILTERS[self.type_combo.currentText()],
                status=STATUS_FILTERS[self.status_combo.currentText()],
                skeleton_type=SKELETON_FILTERS[self.skeleton_combo.currentText()],
                deform_type=DEFORM_FILTERS[self.deform_combo.currentText()],
            )
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Database Error", str(exc))
            return

        self.table.setRowCount(0)
        for row in self._rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            values = [
                row.get("asset_name", ""),
                f"v{int(row.get('version') or 0):03d}",
                str(row.get("asset_type") or ""),
                str(row.get("status") or ""),
                str(row.get("skeleton_type") or ""),
                str(row.get("deform_type") or ""),
                str(row.get("fbx_name") or ""),
                str(row.get("qc_status") or ""),
            ]
            for c, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(value)
                item.setData(QtCore.Qt.UserRole, row.get("asset_version_id"))
                self.table.setItem(r, c, item)
        self._update_selection_state()

    def _selected_rows(self) -> List[Dict]:
        selected_ids: List[int] = []
        for idx in self.table.selectionModel().selectedRows():
            version_id = idx.data(QtCore.Qt.UserRole)
            if version_id:
                selected_ids.append(int(version_id))
        if not selected_ids:
            return []
        by_id = {int(row["asset_version_id"]): row for row in self._rows}
        return [by_id[i] for i in selected_ids if i in by_id]

    def _update_selection_state(self) -> None:
        picked = self._selected_rows()
        if not picked:
            self.load_btn.setEnabled(False)
            self.info_label.setText("Pick one or more animation clips.")
            return
        missing = [row for row in picked if not _exists(_norm_path(row.get("fbx_path")))]
        if missing:
            self.load_btn.setEnabled(False)
            self.info_label.setText("Some selected clips have missing FBX paths.")
            return
        self.load_btn.setEnabled(True)
        self.info_label.setText(f"{len(picked)} animation clips selected.")

    def _set_parm_if_exists(self, parm_name: str, value) -> None:
        parm = self._hda_node.parm(parm_name)
        if parm is not None:
            parm.set(value)

    def _on_load(self) -> None:
        picked = self._selected_rows()
        if not picked:
            QtWidgets.QMessageBox.warning(self, "Validation", "Select at least one animation.")
            return
        for row in picked:
            if not _exists(_norm_path(row.get("fbx_path"))):
                QtWidgets.QMessageBox.warning(self, "Validation", "One or more selected clips are missing on disk.")
                return

        count = len(picked)
        self._set_parm_if_exists("clips", count)
        for i, row in enumerate(picked, start=1):
            clip_path = _norm_path(row.get("fbx_path"))
            clip_name = str(row.get("asset_name") or f"clip{i}")
            self._set_parm_if_exists(f"file{i}", clip_path)
            self._set_parm_if_exists(f"name{i}", clip_name)
            self._set_parm_if_exists(f"source{i}", "fbx")

        # Clear stale clip parms beyond current count.
        clear_idx = count + 1
        while True:
            p = self._hda_node.parm(f"file{clear_idx}")
            n = self._hda_node.parm(f"name{clear_idx}")
            if p is None and n is None:
                break
            if p is not None:
                p.set("")
            if n is not None:
                n.set("")
            clear_idx += 1
        self.accept()


def open_animation_picker(hda_node: hou.Node) -> Optional[Dict]:
    dialog = AnimationPickerDialog(hda_node=hda_node, parent=hou.qt.mainWindow())
    result = dialog.exec_()
    if result != QtWidgets.QDialog.Accepted:
        return None
    picked = dialog._selected_rows()
    return {
        "count": len(picked),
        "animations": [
            {
                "name": Path(str(row.get("fbx_name") or "")).stem or str(row.get("asset_name") or ""),
                "path": _norm_path(row.get("fbx_path")),
                "asset_name": row.get("asset_name", ""),
                "version": int(row.get("version") or 0),
            }
            for row in picked
        ],
    }
