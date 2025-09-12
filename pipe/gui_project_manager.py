import sys
import os
from PySide2 import QtWidgets
from project_manager import Project_Manager

class ProjectManagerGUI(QtWidgets.QWidget):
    def __init__(self):
        super(ProjectManagerGUI, self).__init__()
        self.setWindowTitle("Project Manager")
        self.resize(400, 150)
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        # Show path input
        self.path_layout = QtWidgets.QHBoxLayout()
        self.path_label = QtWidgets.QLabel("Show Path:")
        self.path_edit = QtWidgets.QLineEdit()
        self.path_edit.setText("D:/projects")  # <-- default path here
        self.browse_button = QtWidgets.QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_folder)
        self.path_layout.addWidget(self.path_label)
        self.path_layout.addWidget(self.path_edit)
        self.path_layout.addWidget(self.browse_button)
        self.layout.addLayout(self.path_layout)

        # Show name input
        self.name_layout = QtWidgets.QHBoxLayout()
        self.name_label = QtWidgets.QLabel("Show Name:")
        self.name_edit = QtWidgets.QLineEdit()
        self.name_layout.addWidget(self.name_label)
        self.name_layout.addWidget(self.name_edit)
        self.layout.addLayout(self.name_layout)

        # Create button
        self.create_button = QtWidgets.QPushButton("Create Project")
        self.create_button.clicked.connect(self.create_project)
        self.layout.addWidget(self.create_button)

        # Status
        self.status_label = QtWidgets.QLabel("")
        self.layout.addWidget(self.status_label)

        self.manager = Project_Manager()

    def browse_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.path_edit.setText(folder)

    def create_project(self):
        path = self.path_edit.text()
        show_name = self.name_edit.text()
        if not path or not show_name:
            self.status_label.setText("Please provide both path and show name")
            return
        try:
            self.manager.create_folder_structure(path, show_name)
            self.status_label.setText(f"Project '{show_name}' created successfully!")
        except Exception as e:
            self.status_label.setText(f"Error: {e}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    gui = ProjectManagerGUI()
    gui.show()
    sys.exit(app.exec_())
