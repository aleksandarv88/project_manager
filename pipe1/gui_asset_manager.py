import sys
from PySide2.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton,
                               QVBoxLayout, QComboBox, QMessageBox)
from pathlib import Path
import psycopg2
from asset_manager import Asset_Manager
import shutil

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

        # --- Live asset dropdowns ---
        self.asset_type_live_label = QLabel("Select Asset Type:")
        self.asset_type_live_dropdown = QComboBox()
        self.asset_live_label = QLabel("Select Asset:")
        self.asset_live_dropdown = QComboBox()
        main_layout.addWidget(self.asset_type_live_label)
        main_layout.addWidget(self.asset_type_live_dropdown)
        main_layout.addWidget(self.asset_live_label)
        main_layout.addWidget(self.asset_live_dropdown)

        # --- Live shot dropdowns ---
        self.seq_live_label = QLabel("Select Sequence:")
        self.seq_live_dropdown = QComboBox()
        self.shot_live_label = QLabel("Select Shot:")
        self.shot_live_dropdown = QComboBox()
        main_layout.addWidget(self.seq_live_label)
        main_layout.addWidget(self.seq_live_dropdown)
        main_layout.addWidget(self.shot_live_label)
        main_layout.addWidget(self.shot_live_dropdown)

        # Delete button
        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self.delete_selected)
        main_layout.addWidget(self.delete_button)

        self.setLayout(main_layout)

        # Load initial data
        self.load_projects()
        self.update_fields_visibility()
        self.load_live_asset_types()
        self.load_live_sequences()

        # Connect signals
        self.asset_type_live_dropdown.currentTextChanged.connect(self.load_live_assets)
        self.seq_live_dropdown.currentTextChanged.connect(self.load_live_shots)

    # --- DB connection ---
    def _connect_db(self):
        return psycopg2.connect(
            host=self.db_host,
            database=self.db_name,
            user=self.db_user,
            password=self.db_password
        )

    # --- Project/Sequence loading ---
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

    # --- Field visibility ---
    def update_fields_visibility(self):
        item_type = self.type_dropdown.currentText()
        is_asset = item_type == "asset"
        is_seq = item_type == "sequence"
        is_shot = item_type == "shot"

        # Existing fields
        self.asset_name_label.setVisible(is_asset)
        self.asset_name_input.setVisible(is_asset)
        self.asset_type_label.setVisible(is_asset)
        self.asset_type_dropdown.setVisible(is_asset)
        self.seq_name_label.setVisible(is_seq)
        self.seq_name_input.setVisible(is_seq)
        self.sequence_for_shot_label.setVisible(is_shot)
        self.sequence_for_shot_dropdown.setVisible(is_shot)
        self.shot_name_label.setVisible(is_shot)
        self.shot_name_input.setVisible(is_shot)

        # Live dropdowns visibility
        self.asset_type_live_label.setVisible(is_asset)
        self.asset_type_live_dropdown.setVisible(is_asset)
        self.asset_live_label.setVisible(is_asset)
        self.asset_live_dropdown.setVisible(is_asset)
        self.seq_live_label.setVisible(is_seq)
        self.seq_live_dropdown.setVisible(is_seq)
        self.shot_live_label.setVisible(is_shot)
        self.shot_live_dropdown.setVisible(is_shot)

        # Delete button always visible
        self.delete_button.setVisible(True)

        # Load sequences for shot
        if is_shot:
            project_index = self.project_dropdown.currentIndex()
            if project_index >= 0:
                project_id = self.project_dropdown.itemData(project_index)[0]
                self.load_sequences(project_id)


    # --- Create item ---
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
            self.load_live_asset_types()
            self.load_live_sequences()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # --- Live dropdowns ---
    def load_live_asset_types(self):
        try:
            conn = self._connect_db()
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT type FROM assets ORDER BY type;")
            types = [row[0] for row in cur.fetchall()]
            self.asset_type_live_dropdown.clear()
            self.asset_type_live_dropdown.addItems(types)
            cur.close()
            conn.close()
            if types:
                self.load_live_assets(types[0])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load asset types:\n{e}")

    def load_live_assets(self, asset_type):
        try:
            conn = self._connect_db()
            cur = conn.cursor()
            cur.execute("SELECT name FROM assets WHERE type=%s ORDER BY name;", (asset_type,))
            assets = [row[0] for row in cur.fetchall()]
            self.asset_live_dropdown.clear()
            self.asset_live_dropdown.addItems(assets)
            cur.close()
            conn.close()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load assets:\n{e}")

    def load_live_sequences(self):
        try:
            conn = self._connect_db()
            cur = conn.cursor()
            cur.execute("SELECT name FROM sequences ORDER BY name;")
            seqs = [row[0] for row in cur.fetchall()]
            self.seq_live_dropdown.clear()
            self.seq_live_dropdown.addItems(seqs)
            cur.close()
            conn.close()
            if seqs:
                self.load_live_shots(seqs[0])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load sequences:\n{e}")

    def load_live_shots(self, seq_name):
        try:
            conn = self._connect_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT s.name FROM shots s
                JOIN sequences seq ON s.sequence_id = seq.id
                WHERE seq.name=%s ORDER BY s.name;
            """, (seq_name,))
            shots = [row[0] for row in cur.fetchall()]
            self.shot_live_dropdown.clear()
            self.shot_live_dropdown.addItems(shots)
            cur.close()
            conn.close()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load shots:\n{e}")

    # --- Delete selected ---
    def delete_selected(self):
        item_type = self.type_dropdown.currentText()
        try:
            conn = self._connect_db()
            cur = conn.cursor()

            folder_path = None

            if item_type == "asset":
                asset_name = self.asset_live_dropdown.currentText()
                if not asset_name:
                    QMessageBox.warning(self, "Error", "Select an asset to delete")
                    return

                # Get asset folder path from DB
                cur.execute("SELECT path FROM assets WHERE name=%s;", (asset_name,))
                result = cur.fetchone()
                if result:
                    folder_path = Path(result[0])
                
                cur.execute("DELETE FROM assets WHERE name=%s;", (asset_name,))
                conn.commit()
                QMessageBox.information(self, "Deleted", f"Asset '{asset_name}' deleted")
                self.load_live_assets(self.asset_type_live_dropdown.currentText())

            elif item_type == "sequence":
                seq_name = self.seq_live_dropdown.currentText()
                if not seq_name:
                    QMessageBox.warning(self, "Error", "Select a sequence to delete")
                    return

                # Get sequence folder path from DB
                cur.execute("SELECT path FROM sequences WHERE name=%s;", (seq_name,))
                result = cur.fetchone()
                if result:
                    folder_path = Path(result[0])

                # Optional: delete related shots first
                cur.execute("DELETE FROM shots WHERE sequence_id=(SELECT id FROM sequences WHERE name=%s);", (seq_name,))
                cur.execute("DELETE FROM sequences WHERE name=%s;", (seq_name,))
                conn.commit()
                QMessageBox.information(self, "Deleted", f"Sequence '{seq_name}' deleted")
                self.load_live_sequences()

            elif item_type == "shot":
                shot_name = self.shot_live_dropdown.currentText()
                if not shot_name:
                    QMessageBox.warning(self, "Error", "Select a shot to delete")
                    return

                # Get shot folder path from DB
                cur.execute("SELECT path FROM shots WHERE name=%s;", (shot_name,))
                result = cur.fetchone()
                if result:
                    folder_path = Path(result[0])

                cur.execute("DELETE FROM shots WHERE name=%s;", (shot_name,))
                conn.commit()
                QMessageBox.information(self, "Deleted", f"Shot '{shot_name}' deleted")
                self.load_live_shots(self.seq_live_dropdown.currentText())

            # Remove folder from disk
            if folder_path and folder_path.exists() and folder_path.is_dir():
                shutil.rmtree(folder_path)
                print(f"Deleted folder: {folder_path}")

            cur.close()
            conn.close()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GUIAssetManager()
    window.show()
    sys.exit(app.exec_())
