from PySide2.QtWidgets import QLabel, QLineEdit, QMessageBox
from base_gui import BaseManagerGUI

class SequenceGUI(BaseManagerGUI):
    def __init__(self, asset_manager, db_connect_func):
        super().__init__(asset_manager, db_connect_func, "sequence")

        self.seq_name_label = QLabel("Sequence Name:")
        self.seq_name_input = QLineEdit()
        self.layout.insertWidget(0, self.seq_name_label)
        self.layout.insertWidget(1, self.seq_name_input)

        try:
            self.create_button.clicked.disconnect()
        except Exception:
            pass
        self.create_button.clicked.connect(self.create_item)

    def set_project_dropdown(self, project_dropdown):
        self.project_dropdown = project_dropdown
        self.project_dropdown.currentIndexChanged.connect(self.load_live_items)
        if self.project_dropdown.count() > 0:
            self.project_dropdown.setCurrentIndex(0)
            self.load_live_items()

    def load_live_items(self):
        if not self.project_dropdown or self.project_dropdown.currentIndex() < 0:
            self.live_dropdown.clear()
            return

        project_id, _ = self.project_dropdown.itemData(self.project_dropdown.currentIndex())
        try:
            conn = self._connect_db()
            cur = conn.cursor()
            cur.execute("SELECT name, path FROM sequences WHERE project_id=%s ORDER BY name;", (project_id,))
            items = cur.fetchall()
            self.live_dropdown.clear()
            for name, path in items:
                self.live_dropdown.addItem(name, path)
            cur.close()
            conn.close()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load sequences:\n{e}")

    def create_item(self):
        if not self.project_dropdown or self.project_dropdown.currentIndex() < 0:
            QMessageBox.warning(self, "Error", "Select a project")
            return

        project_id, project_path = self.project_dropdown.itemData(self.project_dropdown.currentIndex())
        seq_name = self.seq_name_input.text().strip()

        if not seq_name:
            QMessageBox.warning(self, "Error", "Sequence name is required!")
            return

        try:
            path = self.am.create_sequence(project_id, project_path, seq_name)
            QMessageBox.information(self, "Success", f"Sequence created at:\n{path}")
            self.load_live_items()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
