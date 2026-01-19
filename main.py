import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import PSFMainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Базовый стиль для темной темы
    app.setStyleSheet("""
        QMainWindow {
            background-color: #2b2b2b;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #555;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
            background-color: #353535;
            color: white;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #88ccff;
        }
        QTableWidget {
            background-color: #1e1e1e;
            color: #ffffff;
            gridline-color: #555;
            alternate-background-color: #252525;
        }
        QTableWidget::item {
            padding: 5px;
        }
        QTableWidget::item:selected {
            background-color: #3a6ea5;
            color: white;
        }
        QHeaderView::section {
            background-color: #353535;
            padding: 8px;
            border: 1px solid #555;
            font-weight: bold;
            color: #88ccff;
        }
        QPushButton {
            background-color: #4a4a4a;
            border: 1px solid #555;
            padding: 8px 16px;
            border-radius: 4px;
            color: white;
            font-weight: bold;
            min-width: 100px;
        }
        QPushButton:hover {
            background-color: #5a5a5a;
            border: 1px solid #666;
        }
        QPushButton:pressed {
            background-color: #3a3a3a;
        }
        QLineEdit, QComboBox {
            background-color: #2b2b2b;
            border: 1px solid #555;
            padding: 6px;
            border-radius: 3px;
            color: white;
            min-height: 25px;
        }
        QLabel {
            color: white;
        }
        QTextEdit {
            background-color: #1e1e1e;
            color: #cccccc;
            border: 1px solid #555;
            font-family: monospace;
        }
        QDockWidget {
            background-color: #353535;
            color: white;
        }
        QMenuBar {
            background-color: #353535;
            color: white;
        }
        QMenu {
            background-color: #353535;
            color: white;
            border: 1px solid #555;
        }
        QToolBar {
            background-color: #353535;
            border: none;
            spacing: 5px;
        }
    """)
    
    w = PSFMainWindow()
    w.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()