import sys
from PySide2.QtWidgets import QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QToolBar, QLabel, QMenu, QDialog, QFormLayout
from PySide2.QtGui import QFont, QIcon
from PySide2.QtCore import Qt

class DetailsWindow(QDialog):
    def __init__(self, item_name, details, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Details for {item_name}")
        self.setGeometry(200, 200, 300, 200)
        self.setStyleSheet("""
            QDialog {
                background-color: #333333;
                color: #ffffff;
            }
            QLabel {
                color: #ff6200;
                font: 10pt Arial;
            }
        """)

        layout = QFormLayout()
        layout.setLabelAlignment(Qt.AlignLeft)
        layout.setSpacing(10)

        # Add details to the form
        layout.addRow("Name:", QLabel(item_name))
        layout.addRow("Price:", QLabel(f"${details['price']:.2f}"))
        layout.addRow("Size:", QLabel(details['size']))
        layout.addRow("Inventory:", QLabel(str(details['inventory'])))

        self.setLayout(layout)

class TreeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dark Grey & Orange Tree App")
        self.setGeometry(100, 100, 800, 600)

        # Sample data for items
        self.item_details = {
            "Fruits": {"price": 0.0, "size": "N/A", "inventory": 0},
            "Apple": {"price": 0.50, "size": "Medium", "inventory": 100},
            "Apple Type 1": {"price": 0.60, "size": "Small", "inventory": 50},
            "Banana": {"price": 0.30, "size": "Large", "inventory": 200},
            "Orange": {"price": 0.40, "size": "Medium", "inventory": 150},
            "Vegetables": {"price": 0.0, "size": "N/A", "inventory": 0},
            "Carrot": {"price": 0.20, "size": "Small", "inventory": 300},
            "Carrot Type 1": {"price": 0.25, "size": "Extra Small", "inventory": 80},
            "Broccoli": {"price": 1.00, "size": "Large", "inventory": 90},
            "Spinach": {"price": 0.80, "size": "Medium", "inventory": 120},
            "Grains": {"price": 0.0, "size": "N/A", "inventory": 0},
            "Wheat": {"price": 2.00, "size": "Bulk", "inventory": 500},
            "Wheat Type 1": {"price": 2.20, "size": "Bulk", "inventory": 200},
            "Rice": {"price": 1.50, "size": "Bulk", "inventory": 400},
            "Oats": {"price": 1.80, "size": "Bulk", "inventory": 300}
        }

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # Add toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        toolbar.setMovable(False)
        toolbar.setStyleSheet("QToolBar { background: #2a2a2a; border: none; padding: 5px; }")
        title_label = QLabel("Tree Explorer")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setStyleSheet("color: #ff6200;")
        toolbar.addWidget(title_label)

        # Create tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Categories")
        self.tree.setFont(QFont("Arial", 10))
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.tree)

        # Apply dark grey and orange stylesheet
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #333333;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 5px;
                padding: 5px;
            }
            QTreeWidget::item {
                padding: 5px;
                height: 30px;
            }
            QTreeWidget::item:hover {
                background-color: #ff6200;
                color: #ffffff;
            }
            QTreeWidget::item:selected {
                background-color: #e55b00;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ff6200;
                border: none;
                padding: 5px;
                font-weight: bold;
            }
        """)

        # Populate tree with sample data
        self.populate_tree()

    def populate_tree(self):
        categories = [
            ("Fruits", "folder"),
            ("Vegetables", "folder"),
            ("Grains", "folder")
        ]
        
        for category, icon in categories:
            parent = QTreeWidgetItem(self.tree)
            parent.setText(0, category)
            parent.setIcon(0, QIcon.fromTheme(icon))
            parent.setExpanded(True)

            if category == "Fruits":
                children = [("Apple", "text-x-generic"), ("Banana", "text-x-generic"), ("Orange", "text-x-generic")]
            elif category == "Vegetables":
                children = [("Carrot", "text-x-generic"), ("Broccoli", "text-x-generic"), ("Spinach", "text-x-generic")]
            else:  # Grains
                children = [("Wheat", "text-x-generic"), ("Rice", "text-x-generic"), ("Oats", "text-x-generic")]

            for child_name, child_icon in children:
                child = QTreeWidgetItem(parent)
                child.setText(0, child_name)
                child.setIcon(0, QIcon.fromTheme(child_icon))

                if child_name in ["Apple", "Carrot", "Wheat"]:
                    sub_child = QTreeWidgetItem(child)
                    sub_child.setText(0, f"{child_name} Type 1")
                    sub_child.setIcon(0, QIcon.fromTheme("text-x-generic"))

    def show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if item:
            menu = QMenu()
            menu.setStyleSheet("""
                QMenu {
                    background-color: #333333;
                    color: #ffffff;
                    border: 1px solid #444444;
                }
                QMenu::item:selected {
                    background-color: #ff6200;
                }
            """)
            view_details_action = menu.addAction("View Details")
            action = menu.exec_(self.tree.viewport().mapToGlobal(position))
            
            if action == view_details_action:
                item_name = item.text(0)
                details = self.item_details.get(item_name, {"price": 0.0, "size": "N/A", "inventory": 0})
                details_window = DetailsWindow(item_name, details, self)
                details_window.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QMainWindow {
            background-color: #2a2a2a;
        }
        QLabel {
            color: #ff6200;
        }
    """)
    window = TreeApp()
    window.show()
    sys.exit(app.exec_())