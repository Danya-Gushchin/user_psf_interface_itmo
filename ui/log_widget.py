from PyQt6.QtWidgets import QTextEdit, QVBoxLayout, QWidget, QGroupBox
from PyQt6.QtCore import QDateTime

class LogWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Лог вычислений", parent)
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setMaximumHeight(150)
        
        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        self.setLayout(layout)
        
    def add_log(self, message: str):
        """Добавить запись в лог"""
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.text_edit.append(f"[{timestamp}] {message}")
        
    def clear_log(self):
        """Очистить лог"""
        self.text_edit.clear()
        
    def log_params(self, params):
        """Записать параметры в лог"""
        self.add_log("=== Параметры вычисления ===")
        self.add_log(f"Размер: {params.size}")
        self.add_log(f"Длина волны: {params.wavelength} мкм")
        self.add_log(f"Задняя апертура: {params.back_aperture}")
        self.add_log(f"Увеличение: {params.magnification}")
        self.add_log(f"Расфокусировка: {params.defocus}")
        self.add_log(f"Астигматизм: {params.astigmatism}")
        self.add_log(f"Диаметр зрачка: {params.pupil_diameter} к.ед.")