from PySide2.QtWidgets import QLabel, QLineEdit, QComboBox, QMessageBox
from base_gui import BaseManagerGUI

class ShotGUI(BaseManagerGUI):
    def __init__(self, asset_manager, db_connect_func):
        super().__init__(asset_manager, db_connect_func, "shot")

        self.seq_label = QLabel("Select Sequence:")
        self.seq_dropdown = QComboBox()
        self.layout.insertWidget(0, self.seq_label)
        self.layout.insertWidget(1, self.seq_dropdown)

        self.shot_name_label = QLabel("Shot Name:")
        self.shot_name_input = QLineEdit()
        self.layout.insertWidget(2, self.shot_name_label)
        self.layout.insertWidget(3, self.shot_name_input)

        try:
            self.create_button.clicked.disconnect()
        except Exception:
            pass
        self.create_button.clicked.connect(self.create_item)

        self.seq_dropdown.currentIndexChanged.connect(self.load_live_items)

    def set_project_dropdown(self, project_dropdown):
        self.project_dropdown = project_dropdown
        self.project_dropdown.currentIndexChanged.connect(self.load_sequences)
        if self.project_dropdown.count() > 0:
            self.project_dropdown.setCurrentIndex(0)
            self.load_sequences()

    def load_sequences(self):
        self.seq_dropdown.clear()
        if not self.project_dropdown or self.project_dropdown.currentIndex() < 0:
            return

        project_id, _ = self.project_dropdown.itemData(self.project_dropdown.currentIndex())
        try:
            conn = self._connect_db()
            cur = conn.cursor()
            cur.execute("SELECT id, name, path FROM sequences WHERE project_id=%s ORDER BY name;", (project_id,))
            sequences = cur.fetchall()
            for seq_id, name, path in sequences:
                self.seq_dropdown.addItem(name, (seq_id, path))
            cur.close()
            conn.close()
            if self.seq_dropdown.count() > 0:
                self.seq_dropdown.setCurrentIndex(0)
                self.load_live_items()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load sequences:\n{e}")

    def load_live_items(self):
        self.live_dropdown.clear()
        if self.seq_dropdown.currentIndex() < 0:
            return

        seq_id, seq_path = self.seq_dropdown.itemData(self.seq_dropdown.currentIndex())
        try:
            conn = self._connect_db()
            cur = conn.cursor()
            cur.execute("SELECT name, path FROM shots WHERE sequence_id=%s ORDER BY name;", (seq_id,))
            shots = cur.fetchall()
            for name, path in shots:
                self.live_dropdown.addItem(name, path)
            cur.close()
            conn.close()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load shots:\n{e}")

    def create_item(self):
        if self.seq_dropdown.currentIndex() < 0:
            QMessageBox.warning(self, "Error", "Select a sequence")
            return

        seq_id, seq_path = self.seq_dropdown.itemData(self.seq_dropdown.currentIndex())
        shot_name = self.shot_name_input.text().strip()

        if not shot_name:
            QMessageBox.warning(self, "Error", "Shot name is required!")
            return

        try:
            path = self.am.create_shot(seq_id, seq_path, shot_name)
            QMessageBox.information(self, "Success", f"Shot created at:\n{path}")
            self.load_live_items()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
