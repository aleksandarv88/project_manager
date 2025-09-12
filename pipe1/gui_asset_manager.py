import sys
from PySide2.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton,
                               QVBoxLayout, QComboBox, QMessageBox)
from pathlib import Path
import psycopg2
from asset_manager import Asset_Manager

class GUIAssetManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Asset/Sequence/Shot Manager")
        self.am = Asset_Manager()

        # DB connection info
        self.db_host = "localhost"
        self.db_name = "FX3X"
        self.db_user = "postgres"
        self.db_password = "Ifmatoodlon@321"

        main_layout = QVBoxLayout()

        # Project selection
        self.project_label = QLabel("Select Project:")
        self.project_dropdown = QComboBox()
        main_layout.addWidget(self.project_label)
        main_layout.addWidget(self.project_dropdown)

        # Type selection
        self.type_label = QLabel("Type:")
        self.type_dropdown = QComboBox()
        self.type_dropdown.addItems(["asset", "sequence", "shot"])
        self.type_dropdown.currentIndexChanged.connect(self.update_fields_visibility)
        main_layout.addWidget(self.type_label)
        main_layout.addWidget(self.type_dropdown)

        # Asset fields
        self.asset_name_label = QLabel("Asset Name:")
        self.asset_name_input = QLineEdit()
        self.asset_type_label = QLabel("Asset Type:")
        self.asset_type_dropdown = QComboBox()
        self.asset_type_dropdown.addItems(["props", "env", "vehicle", "fx", "other"])

        main_layout.addWidget(self.asset_name_label)
        main_layout.addWidget(self.asset_name_input)
        main_layout.addWidget(self.asset_type_label)
        main_layout.addWidget(self.asset_type_dropdown)

        # Sequence fields
        self.seq_name_label = QLabel("Sequence Name:")
        self.seq_name_input = QLineEdit()
        main_layout.addWidget(self.seq_name_label)
        main_layout.addWidget(self.seq_name_input)

        # Shot fields
        self.shot_name_label = QLabel("Shot Name:")
        self.shot_name_input = QLineEdit()
        self.sequence_for_shot_label = QLabel("Select Sequence:")
        self.sequence_for_shot_dropdown = QComboBox()
        main_layout.addWidget(self.sequence_for_shot_label)
        main_layout.addWidget(self.sequence_for_shot_dropdown)
        main_layout.addWidget(self.shot_name_label)
        main_layout.addWidget(self.shot_name_input)

        # Create button
        self.create_button = QPushButton("Create")
        self.create_button.clicked.connect(self.create_item)
        main_layout.addWidget(self.create_button)

        self.setLayout(main_layout)

        self.load_projects()
        self.update_fields_visibility()

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

    def load_sequences(self, project_id):
        try:
            conn = self._connect_db()
            cur = conn.cursor()
            cur.execute("SELECT id, name, path FROM sequences WHERE project_id=%s ORDER BY id;", (project_id,))
            sequences = cur.fetchall()
            cur.close()
            conn.close()

            self.sequence_for_shot_dropdown.clear()
            for sid, name, path in sequences:
                self.sequence_for_shot_dropdown.addItem(name, (sid, path))

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load sequences:\n{e}")

    def update_fields_visibility(self):
        item_type = self.type_dropdown.currentText()
        is_asset = item_type == "asset"
        is_seq = item_type == "sequence"
        is_shot = item_type == "shot"

        # Asset
        self.asset_name_label.setVisible(is_asset)
        self.asset_name_input.setVisible(is_asset)
        self.asset_type_label.setVisible(is_asset)
        self.asset_type_dropdown.setVisible(is_asset)

        # Sequence
        self.seq_name_label.setVisible(is_seq)
        self.seq_name_input.setVisible(is_seq)

        # Shot
        self.sequence_for_shot_label.setVisible(is_shot)
        self.sequence_for_shot_dropdown.setVisible(is_shot)
        self.shot_name_label.setVisible(is_shot)
        self.shot_name_input.setVisible(is_shot)

        # Load sequences for selected project if shot selected
        if is_shot:
            project_index = self.project_dropdown.currentIndex()
            if project_index >= 0:
                project_id = self.project_dropdown.itemData(project_index)[0]
                self.load_sequences(project_id)

    def create_item(self):
        project_index = self.project_dropdown.currentIndex()
        if project_index < 0:
            QMessageBox.warning(self, "Error", "Select a project")
            return

        project_id, project_path = self.project_dropdown.itemData(project_index)
        item_type = self.type_dropdown.currentText()

        try:
            if item_type == "asset":
                asset_name = self.asset_name_input.text().strip()
                asset_type = self.asset_type_dropdown.currentText()
                path = self.am.create_asset(project_id, project_path, asset_name=asset_name, asset_type=asset_type)
            elif item_type == "sequence":
                seq_name = self.seq_name_input.text().strip()
                path = self.am.create_sequence(project_id, project_path, seq_name)
            else:  # shot
                seq_index = self.sequence_for_shot_dropdown.currentIndex()
                if seq_index < 0:
                    QMessageBox.warning(self, "Error", "Select a sequence for the shot")
                    return
                seq_id, seq_path = self.sequence_for_shot_dropdown.itemData(seq_index)
                shot_name = self.shot_name_input.text().strip()
                path = self.am.create_shot(seq_id, seq_path, shot_name)

            QMessageBox.information(self, "Success", f"{item_type.title()} created at:\n{path}")
            self.update_fields_visibility()  # refresh sequences if needed

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GUIAssetManager()
    window.show()
    sys.exit(app.exec_())
