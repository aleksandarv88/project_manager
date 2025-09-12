# main_gui.py
import sys
from PySide2.QtWidgets import QApplication, QWidget, QVBoxLayout, QTabWidget, QLabel, QComboBox, QMessageBox
from asset_gui import AssetGUI
from seq_gui import SequenceGUI
from shot_gui import ShotGUI
from asset_manager import Asset_Manager
import psycopg2

class MainGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pipeline Manager")
        self.am = Asset_Manager(self._connect_db)
        self.db_host = "localhost"
        self.db_name = "FX3X"
        self.db_user = "postgres"
        self.db_password = "Ifmatoodlon@321"

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Project dropdown
        self.project_label = QLabel("Select Project:")
        self.project_dropdown = QComboBox()
        layout.addWidget(self.project_label)
        layout.addWidget(self.project_dropdown)
        self.load_projects()

        # Tabs
        tabs = QTabWidget()
        self.asset_tab = AssetGUI(self.am, self._connect_db)
        self.seq_tab   = SequenceGUI(self.am, self._connect_db)
        self.shot_tab  = ShotGUI(self.am, self._connect_db)

        # Assign project dropdowns to tabs
        self.asset_tab.set_project_dropdown(self.project_dropdown)
        self.seq_tab.set_project_dropdown(self.project_dropdown)
        self.shot_tab.set_project_dropdown(self.project_dropdown)

        # Add tabs
        tabs.addTab(self.asset_tab, "Assets")
        tabs.addTab(self.seq_tab, "Sequences")
        tabs.addTab(self.shot_tab, "Shots")
        layout.addWidget(tabs)

    def _connect_db(self):
        return psycopg2.connect(
            host=self.db_host,
            database=self.db_name,
            user=self.db_user,
            password=self.db_password
        )

    def load_projects(self):
        try:
            conn = self._connect_db()
            cur = conn.cursor()
            cur.execute("SELECT id, name, path FROM projects ORDER BY id;")
            projects = cur.fetchall()
            cur.close()
            conn.close()

            self.project_dropdown.clear()
            for pid, name, path in projects:
                self.project_dropdown.addItem(name, (pid, path))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load projects:\n{e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainGUI()
    window.show()
    sys.exit(app.exec_())
