import sys
from PySide2.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton,
                               QFileDialog, QVBoxLayout, QMessageBox, QComboBox)
from project_manager import Project_Manager
from pathlib import Path
import psycopg2

class GUIAssetManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Asset Manager")
        self.pm = Project_Manager()

        layout = QVBoxLayout()

        # Show name
        self.name_label = QLabel("Show Name:")
        self.name_input = QLineEdit()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)

        # Show root path (read-only)
        self.path_label = QLabel("Show Root Path:")
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        layout.addWidget(self.path_label)
        layout.addWidget(self.path_input)

        # Browse button
        self.browse_button = QPushButton("Browse Folder")
        self.browse_button.clicked.connect(self.browse_folder)
        layout.addWidget(self.browse_button)

        # Create button
        self.create_button = QPushButton("Create Project")
        self.create_button.clicked.connect(self.create_project)
        layout.addWidget(self.create_button)

        # Dropdown for all projects
        self.projects_label = QLabel("All Projects:")
        self.projects_dropdown = QComboBox()
        self.projects_dropdown.setEditable(False)
        self.projects_dropdown.currentIndexChanged.connect(self.populate_fields_from_dropdown)
        layout.addWidget(self.projects_label)
        layout.addWidget(self.projects_dropdown)

        self.setLayout(layout)

        # Load existing projects
        self.refresh_projects_dropdown()

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Show Root Folder")
        if folder:
            # Normalize path with pathlib
            folder_path = Path(folder).as_posix()
            self.path_input.setText(folder_path)

    def create_project(self):
        name = self.name_input.text().strip()
        path = self.path_input.text().strip()
        if not name or not path:
            QMessageBox.warning(self, "Error", "Please enter both show name and root path")
            return

        try:
            self.pm.create_project(name, path)
            QMessageBox.information(self, "Success", f"Project '{name}' created!")
            self.refresh_projects_dropdown()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def refresh_projects_dropdown(self):
        """Fetch all projects from DB and populate dropdown."""
        try:
            conn = psycopg2.connect(
                host=self.pm.host,
                database=self.pm.db_name,
                user=self.pm.user,
                password=self.pm.password
            )
            cur = conn.cursor()
            cur.execute("SELECT name, path FROM projects ORDER BY id;")
            projects = cur.fetchall()
            cur.close()
            conn.close()

            self.projects_dropdown.clear()
            for name, path in projects:
                self.projects_dropdown.addItem(name, path)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load projects:\n{e}")

    def populate_fields_from_dropdown(self, index):
        """Fill name and path fields when selecting a project."""
        if index < 0:
            return
        #name = self.projects_dropdown.itemText(index)
        #path = self.projects_dropdown.itemData(index)
        #self.name_input.setText(name)
        #self.path_input.setText(path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GUIAssetManager()
    window.show()
    sys.exit(app.exec_())
