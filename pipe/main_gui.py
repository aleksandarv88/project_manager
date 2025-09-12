import sys
from PySide2.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QFileDialog, QMessageBox
)
from asset_manager import AssetManager  # updated backend import


class PipelineGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pipeline Project & Asset Manager")
        self.setMinimumWidth(500)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self._setup_project_section()
        self._setup_asset_section()

    # ----------------------
    # Project Section
    # ----------------------
    def _setup_project_section(self):
        project_layout = QVBoxLayout()
        self.layout.addLayout(project_layout)

        project_label = QLabel("Project (Show) Path:")
        project_layout.addWidget(project_label)

        path_layout = QHBoxLayout()
        self.show_path_field = QLineEdit()
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_show_path)
        path_layout.addWidget(self.show_path_field)
        path_layout.addWidget(browse_button)

        project_layout.addLayout(path_layout)

    def browse_show_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Show Folder")
        if folder:
            self.show_path_field.setText(folder)

    # ----------------------
    # Asset Section
    # ----------------------
    def _setup_asset_section(self):
        asset_layout = QVBoxLayout()
        self.layout.addLayout(asset_layout)

        asset_label = QLabel("Create Asset:")
        asset_layout.addWidget(asset_label)

        # Asset Type
        type_layout = QHBoxLayout()
        type_label = QLabel("Asset Type:")
        self.asset_type_combo = QComboBox()
        self.asset_type_combo.addItems(AssetManager.ASSET_TYPES)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.asset_type_combo)
        asset_layout.addLayout(type_layout)

        # Asset Name
        name_layout = QHBoxLayout()
        name_label = QLabel("Asset Name:")
        self.asset_name_field = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.asset_name_field)
        asset_layout.addLayout(name_layout)

        # Create Button
        create_button = QPushButton("Create Asset")
        create_button.clicked.connect(self.create_asset_callback)
        asset_layout.addWidget(create_button)

    def create_asset_callback(self):
        show_path = self.show_path_field.text()
        asset_type = self.asset_type_combo.currentText()
        asset_name = self.asset_name_field.text().strip()

        if not show_path or not asset_name:
            QMessageBox.warning(self, "Input Error", "Please provide show path and asset name.")
            return

        try:
            am = AssetManager(show_path)
            am.create_asset(asset_type, asset_name)
            QMessageBox.information(
                self,
                "Success",
                f"Asset '{asset_name}' created under '{asset_type}'!"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# ----------------------
# Run the GUI
# ----------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = PipelineGUI()
    gui.show()
    sys.exit(app.exec_())
