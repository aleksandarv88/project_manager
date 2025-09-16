import sys
import os
import psycopg2
from PySide2.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide2.QtCore import Qt

# ---------- CONFIG ----------
DB_NAME = "FX3X"
DB_USER = "your_user"
DB_PASSWORD = "your_password"
DB_HOST = "localhost"
DB_PORT = "5432"
# ---------------------------

class FX3XManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FX3X Artist Manager")

        self.conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
            host=DB_HOST, port=DB_PORT
        )

        layout = QVBoxLayout(self)

        # Top: Artist dropdown
        artist_layout = QHBoxLayout()
        artist_layout.addWidget(QLabel("Select Artist:"))
        self.artist_combo = QComboBox()
        self.artist_combo.currentIndexChanged.connect(self.load_tasks)
        artist_layout.addWidget(self.artist_combo)
        layout.addLayout(artist_layout)

        # Middle: Tasks table
        self.tasks_table = QTableWidget(0, 4)
        self.tasks_table.setHorizontalHeaderLabels(["Task ID", "Asset", "Shot", "Task Type"])
        self.tasks_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tasks_table.itemSelectionChanged.connect(self.load_task_details)
        layout.addWidget(QLabel("Tasks:"))
        layout.addWidget(self.tasks_table)

        # Right side: Task details & software
        detail_layout = QHBoxLayout()

        self.software_combo = QComboBox()
        self.software_combo.currentIndexChanged.connect(self.load_scenes)
        detail_layout.addWidget(QLabel("Software:"))
        detail_layout.addWidget(self.software_combo)

        self.scenes_table = QTableWidget(0, 1)
        self.scenes_table.setHorizontalHeaderLabels(["Scene Files"])
        self.scenes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        detail_layout.addWidget(self.scenes_table)
        layout.addWidget(QLabel("Softwares & Scenes:"))
        layout.addLayout(detail_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start from Scratch")
        self.launch_btn = QPushButton("Launch Selected Scene")
        self.launch_btn.clicked.connect(self.launch_scene)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.launch_btn)
        layout.addLayout(btn_layout)

        self.load_artists()

    def query(self, sql, params=None):
        with self.conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()

    def load_artists(self):
        self.artist_combo.clear()
        artists = self.query("SELECT id, username FROM core_artist ORDER BY username;")
        for artist in artists:
            self.artist_combo.addItem(artist[1], artist[0])
        if artists:
            self.load_tasks()

    def load_tasks(self):
        artist_id = self.artist_combo.currentData()
        if not artist_id:
            return
        tasks = self.query("""
            SELECT id,
                   (SELECT name FROM core_asset WHERE core_asset.id=asset_id) AS asset_name,
                   (SELECT name FROM core_shot WHERE core_shot.id=shot_id) AS shot_name,
                   task_type
            FROM core_task WHERE artist_id=%s
            ORDER BY id DESC;
        """, (artist_id,))
        self.tasks_table.setRowCount(0)
        for row_data in tasks:
            row = self.tasks_table.rowCount()
            self.tasks_table.insertRow(row)
            for col, val in enumerate(row_data):
                self.tasks_table.setItem(row, col, QTableWidgetItem(str(val or "")))
        self.software_combo.clear()
        self.scenes_table.setRowCount(0)

    def load_task_details(self):
        # Simulate loading softwares based on task_type (you can query your DB or config)
        selected_items = self.tasks_table.selectedItems()
        if not selected_items:
            return
        task_id = selected_items[0].text()
        # Example: if task_type is FX -> Houdini, else -> Maya
        task_type = selected_items[3].text().lower()
        self.software_combo.clear()
        if "fx" in task_type:
            self.software_combo.addItems(["Houdini", "Maya"])
        elif "mod" in task_type or "model" in task_type:
            self.software_combo.addItems(["Maya"])
        else:
            self.software_combo.addItems(["Houdini", "Maya"])

        self.load_scenes()

    def load_scenes(self):
        # Show dummy scenes for demo; in your real app read file system from DB path
        self.scenes_table.setRowCount(0)
        sw = self.software_combo.currentText()
        if not sw:
            return
        # Here you’d actually read from your filesystem for that software’s folder
        example_files = []
        if sw.lower() == "houdini":
            example_files = ["houdini_scene1.hip", "houdini_scene2.hip"]
        elif sw.lower() == "maya":
            example_files = ["maya_scene1.mb", "maya_scene2.mb"]

        for f in example_files:
            row = self.scenes_table.rowCount()
            self.scenes_table.insertRow(row)
            self.scenes_table.setItem(row, 0, QTableWidgetItem(f))

    def launch_scene(self):
        selected_items = self.scenes_table.selectedItems()
        if not selected_items:
            return
        scene = selected_items[0].text()
        # Replace this with launching Maya/Houdini
        print(f"Launching scene: {scene}")
        os.startfile(scene)  # only works on Windows if path exists

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FX3XManager()
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec_())
