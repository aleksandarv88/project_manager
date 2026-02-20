from __future__ import annotations


def apply_stylesheet(app) -> None:
    app.setStyleSheet(
        """
        QWidget {
            background-color: #1f1f22;
            color: #f0f0f0;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 12pt;
        }
        #HeaderLabel {
            font-size: 24pt;
            font-weight: 600;
            color: #ff8800;
        }
        #SectionLabel {
            font-size: 14pt;
            font-weight: 600;
            margin-bottom: 4px;
        }
        #FieldLabel {
            font-weight: 600;
            color: #ffa64d;
        }
        #DetailValue {
            font-size: 11pt;
        }
        QFrame#Card {
            background-color: #2a2a2e;
            border-radius: 12px;
            border: 1px solid #3c3c42;
        }
        QComboBox, QLineEdit, QPlainTextEdit, QTextEdit {
            background-color: #343438;
            border: 1px solid #4c4c52;
            border-radius: 6px;
            padding: 6px 8px;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox QAbstractItemView {
            background-color: #2f2f33;
            color: #f6f6f6;
            selection-background-color: #ff8800;
            selection-color: #101010;
        }
        QTabWidget::pane {
            border: 1px solid #35353a;
            border-radius: 8px;
        }
        QTabBar::tab {
            background-color: #303035;
            color: #f0f0f0;
            padding: 8px 14px;
            border: 1px solid #3c3c42;
            border-bottom: none;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #ff8800;
            color: #101010;
        }
        QTableWidget {
            background-color: #1f1f23;
            alternate-background-color: #26262a;
            gridline-color: #3e3e42;
            border: 1px solid #35353a;
            border-radius: 8px;
        }
        QHeaderView::section {
            background-color: #303035;
            color: #f0f0f0;
            padding: 6px;
            border: none;
        }
        QTableWidget::item:selected {
            background-color: #ff8800;
            color: #101010;
        }
        QPushButton {
            background-color: #ff8800;
            color: #101010;
            border: none;
            border-radius: 8px;
            padding: 8px 14px;
            font-weight: 600;
        }
        QPushButton:disabled {
            background-color: #3d3d42;
            color: #7a7a7f;
        }
        QPushButton:hover:!disabled {
            background-color: #ffa347;
        }
        QPushButton:pressed:!disabled {
            background-color: #cc6b00;
        }
        QMessageBox {
            background-color: #2a2a2e;
        }
        """
    )
