import sys
import os
import subprocess
from PySide2 import QtWidgets, QtCore

class HoudiniLauncher(QtWidgets.QWidget):
    def __init__(self):
        super(HoudiniLauncher, self).__init__()

        self.setWindowTitle("Houdini Launcher")
        self.setFixedSize(300, 200)

        # Labels + LineEdits
        self.show_edit = QtWidgets.QLineEdit()
        self.shot_edit = QtWidgets.QLineEdit()
        self.asset_edit = QtWidgets.QLineEdit()

        form = QtWidgets.QFormLayout()
        form.addRow("Show:", self.show_edit)
        form.addRow("Shot:", self.shot_edit)
        form.addRow("Asset:", self.asset_edit)

        # Launch button
        self.launch_btn = QtWidgets.QPushButton("Launch Houdini")
        self.launch_btn.clicked.connect(self.launch_houdini)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.launch_btn)
        self.setLayout(layout)

    def launch_houdini(self):
        show = self.show_edit.text().strip()
        shot = self.shot_edit.text().strip()
        asset = self.asset_edit.text().strip()

        if not show or not shot:
            QtWidgets.QMessageBox.warning(self, "Missing info", "Show and Shot are required.")
            return

        # Set environment
        os.environ["SHOW"] = show
        os.environ["SHOT"] = shot
        os.environ["ASSET"] = asset

        # Optional: extend PYTHONPATH
        #tools_path = r"D:/pipeline/tools"
        #os.environ["PYTHONPATH"] = tools_path + ";" + os.environ.get("PYTHONPATH", "")

        # Launch Houdini
        houdini_exe = r"C:\Program Files\Side Effects Software\Houdini 21.0.440\bin\houdini.exe"
        subprocess.Popen([houdini_exe])

        self.close()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = HoudiniLauncher()
    win.show()
    sys.exit(app.exec_())
