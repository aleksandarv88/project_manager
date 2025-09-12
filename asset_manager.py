from pathlib import Path
from PySide2 import QtWidgets, QtCore

# Departments every asset should get
DEPARTMENTS = ["mod", "ldev", "anim", "fx", "lgt", "cfx", "layout", "env"]

# Department folder template
DEPARTMENT_TEMPLATE = {
    "software": {
        "artist_name": {
            "usd": {
                "data": {}
            }
        }
    }
}

# Helper function
def create_recursive(base: Path, struct: dict):
    """Recursively create folders from nested dict structure."""
    for name, subtree in struct.items():
        target = base / name
        target.mkdir(parents=True, exist_ok=True)
        if isinstance(subtree, dict) and subtree:
            create_recursive(target, subtree)


def create_asset(show_path: str, asset_type: str, asset_name: str):
    """Creates an asset folder structure under the show folder."""
    asset_root = Path(show_path) / "assets" / asset_type / asset_name
    asset_root.mkdir(parents=True, exist_ok=True)

    # Create departments
    for dep in DEPARTMENTS:
        dep_root = asset_root / dep
        create_recursive(dep_root, DEPARTMENT_TEMPLATE)


# -------------------- GUI --------------------
class AssetManagerGUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Asset Manager")
        self.setMinimumSize(400, 200)
        self.build_ui()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Show path
        self.show_path_edit = QtWidgets.QLineEdit()
        browse_btn = QtWidgets.QPushButton("Browse Show Folder")
        browse_btn.clicked.connect(self.browse_show)
        show_layout = QtWidgets.QHBoxLayout()
        show_layout.addWidget(self.show_path_edit)
        show_layout.addWidget(browse_btn)

        # Asset Type
        self.asset_type_combo = QtWidgets.QComboBox()
        self.asset_type_combo.addItems(["props", "env", "vehicle", "fx"])
        asset_type_layout = QtWidgets.QHBoxLayout()
        asset_type_layout.addWidget(QtWidgets.QLabel("Asset Type:"))
        asset_type_layout.addWidget(self.asset_type_combo)

        # Asset Name
        self.asset_name_edit = QtWidgets.QLineEdit()
        asset_name_layout = QtWidgets.QHBoxLayout()
        asset_name_layout.addWidget(QtWidgets.QLabel("Asset Name:"))
        asset_name_layout.addWidget(self.asset_name_edit)

        # Create button
        create_btn = QtWidgets.QPushButton("Create Asset")
        create_btn.clicked.connect(self.on_create_asset)

        # Add to main layout
        layout.addLayout(show_layout)
        layout.addLayout(asset_type_layout)
        layout.addLayout(asset_name_layout)
        layout.addWidget(create_btn)

    def browse_show(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Show Folder")
        if folder:
            self.show_path_edit.setText(folder)

    def on_create_asset(self):
        show_path = self.show_path_edit.text().strip()
        asset_type = self.asset_type_combo.currentText()
        asset_name = self.asset_name_edit.text().strip()

        if not show_path or not asset_name:
            QtWidgets.QMessageBox.warning(self, "Error", "Please provide show path and asset name")
            return

        try:
            create_asset(show_path, asset_type, asset_name)
            QtWidgets.QMessageBox.information(self, "Success", f"Asset '{asset_name}' created under {asset_type}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    gui = AssetManagerGUI()
    gui.show()
    app.exec_()
