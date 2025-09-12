from PySide2.QtWidgets import QWidget, QVBoxLayout, QComboBox, QPushButton, QMessageBox

class BaseManagerGUI(QWidget):
    def __init__(self, asset_manager, db_connect_func, item_type):
        super().__init__()
        self.am = asset_manager
        self._connect_db = db_connect_func
        self.item_type = item_type

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.live_dropdown = QComboBox()
        self.layout.addWidget(self.live_dropdown)

        self.create_button = QPushButton("Create")
        self.layout.addWidget(self.create_button)

        self.delete_button = QPushButton("Delete Selected")
        self.layout.addWidget(self.delete_button)
        self.delete_button.clicked.connect(self.delete_item)

    def delete_item(self):
        index = self.live_dropdown.currentIndex()
        if index < 0:
            QMessageBox.warning(self, "Error", "Select an item to delete")
            return

        path = self.live_dropdown.itemData(index)
        try:
            self.am.delete_item(path)
            self.live_dropdown.removeItem(index)
            QMessageBox.information(self, "Success", f"{self.item_type.title()} deleted:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
