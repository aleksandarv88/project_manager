from PySide2 import QtWidgets
import sys
import subprocess
import os

HOUDINI_EXE = "C:/Program Files/Side Effects Software/Houdini 21.0.440/bin/houdini.exe"
HOUDINI_EXE = os.path.normpath(HOUDINI_EXE)

print(HOUDINI_EXE)

class HoudiniLauncher(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Houdini Launcher")

        # Layout
        layout = QtWidgets.QVBoxLayout(self)

        # Line edit за пат до сцена
        self.scene_path = QtWidgets.QLineEdit(self)
        layout.addWidget(self.scene_path)

        # Browse button
        browse_btn = QtWidgets.QPushButton("Browse Scene", self)
        browse_btn.clicked.connect(self.browse_scene)
        layout.addWidget(browse_btn)

        # Launch button
        launch_btn = QtWidgets.QPushButton("Launch Houdini", self)
        launch_btn.clicked.connect(self.launch_houdini)
        layout.addWidget(launch_btn)

    def browse_scene(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Houdini Scene",
            "",
            "Houdini Files (*.hip *.hiplc);;All Files (*)"
        )
        if filename:
            print("filename:"+filename)
            self.scene_path.setText(filename)

    def launch_houdini(self):
        hip_file = self.scene_path.text().replace('/', '\\')
        if hip_file:
            # cmd /c start launches a completely independent process
            cmd = f'cmd /c start "" "{HOUDINI_EXE}" "{hip_file}"'
            subprocess.Popen(cmd, shell=True)
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Select a Houdini scene first!")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = HoudiniLauncher()
    window.show()
    sys.exit(app.exec_())
