#USE create folder structure.py
from PySide2 import QtWidgets
import sys, os

PROJECTS_ROOT = "D:/projects/shows"

class ProjectManager(QtWidgets.QWidget):
    def __init__(self):
        super(ProjectManager, self).__init__()
        self.setWindowTitle("Project Manager")
        self.setMinimumWidth(300)

        layout = QtWidgets.QVBoxLayout(self)

        # Show field
        self.show_field = QtWidgets.QLineEdit()
        self.show_field.setPlaceholderText("Enter show name")
        layout.addWidget(QtWidgets.QLabel("Show:"))
        layout.addWidget(self.show_field)

        self.create_show_btn = QtWidgets.QPushButton("Create Show")
        layout.addWidget(self.create_show_btn)
        self.create_show_btn.clicked.connect(self.create_show)

        # Asset field
        self.asset_field = QtWidgets.QLineEdit()
        self.asset_field.setPlaceholderText("Enter asset name")
        layout.addWidget(QtWidgets.QLabel("Asset:"))
        layout.addWidget(self.asset_field)

        self.create_asset_btn = QtWidgets.QPushButton("Create Asset")
        layout.addWidget(self.create_asset_btn)
        self.create_asset_btn.clicked.connect(self.create_asset)

        # Shot field
        self.shot_field = QtWidgets.QLineEdit()
        self.shot_field.setPlaceholderText("Enter shot name")
        layout.addWidget(QtWidgets.QLabel("Shot:"))
        layout.addWidget(self.shot_field)

        self.create_shot_btn = QtWidgets.QPushButton("Create Shot")
        layout.addWidget(self.create_shot_btn)
        self.create_shot_btn.clicked.connect(self.create_shot)

    def create_show(self):
        show = self.show_field.text().strip()
        if not show:
            QtWidgets.QMessageBox.warning(self, "Error", "Please enter a show name")
            return
        show_path = os.path.join(PROJECTS_ROOT, show)
        os.makedirs(show_path, exist_ok=True)
        for sub in ["assets/char", "assets/props", "assets/env",
                    "shots/seq001/sh001", "houdini", "cache", "reference"]:
            os.makedirs(os.path.join(show_path, sub), exist_ok=True)
        QtWidgets.QMessageBox.information(self, "Done", f"Created show: {show}")

    def create_asset(self):
        show = self.show_field.text().strip()
        asset = self.asset_field.text().strip()
        if not show or not asset:
            QtWidgets.QMessageBox.warning(self, "Error", "Enter show + asset name")
            return
        path = os.path.join(PROJECTS_ROOT, show, "assets", asset)
        os.makedirs(path, exist_ok=True)
        for sub in ["model", "rig", "lookdev", "cache"]:
            os.makedirs(os.path.join(path, sub), exist_ok=True)
        QtWidgets.QMessageBox.information(self, "Done", f"Created asset: {asset}")

    def create_shot(self):
        show = self.show_field.text().strip()
        shot = self.shot_field.text().strip()
        if not show or not shot:
            QtWidgets.QMessageBox.warning(self, "Error", "Enter show + shot name")
            return
        path = os.path.join(PROJECTS_ROOT, show, "shots", shot)
        os.makedirs(path, exist_ok=True)
        for sub in ["layout", "animation", "fx", "lighting", "comp"]:
            os.makedirs(os.path.join(path, sub), exist_ok=True)
        QtWidgets.QMessageBox.information(self, "Done", f"Created shot: {shot}")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = ProjectManager()
    win.show()
    sys.exit(app.exec_())
