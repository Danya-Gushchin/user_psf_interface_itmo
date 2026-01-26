"""
Диалог прогресса вычислений с возможностью отмены
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, 
    QProgressBar, QLabel, QPushButton
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
import time


class CalculationWorker(QThread):
    """Поток для выполнения вычислений в фоне"""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    time_updated = pyqtSignal(str)
    calculation_finished = pyqtSignal(bool)
    
    def __init__(self, table_widget, rows_to_calculate):
        super().__init__()
        self.table_widget = table_widget
        self.rows_to_calculate = rows_to_calculate
        self.is_canceled = False
        
    def run(self):
        """Выполнение вычислений"""
        start_time = time.time()
        total = len(self.rows_to_calculate)
        
        try:
            for i, row in enumerate(self.rows_to_calculate):
                if self.is_canceled:
                    self.calculation_finished.emit(False)
                    return
                
                # Обновление статуса
                self.status_updated.emit(f"Обработка строки {row + 1} ({i + 1} из {total})")
                
                # Выполнение расчета
                self.table_widget._calculate_row(row)
                
                # Обновление прогресса
                self.progress_updated.emit(i + 1)
                
                # Обновление времени
                elapsed = time.time() - start_time
                if i > 0:
                    avg_time = elapsed / (i + 1)
                    remaining = avg_time * (total - i - 1)
                    self.time_updated.emit(
                        f"Прошло: {elapsed:.1f}с | Осталось: ~{remaining:.1f}с"
                    )
            
            self.calculation_finished.emit(True)
            
        except Exception as e:
            print(f"Ошибка при вычислении: {e}")
            self.calculation_finished.emit(False)
    
    def cancel(self):
        """Отмена вычислений"""
        self.is_canceled = True


class ProgressDialog(QDialog):
    """Диалоговое окно с прогресс-баром и кнопкой отмены"""
    
    def __init__(self, parent=None, title="Вычисление", max_value=100):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(450)
        self.is_canceled = False
        self.worker = None
        
        self.setup_ui(max_value)
        
    def setup_ui(self, max_value):
        """Настройка интерфейса диалога"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        self.title_label = QLabel("Выполняется расчет ФРТ...")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        layout.addWidget(self.title_label)
        
        # Текст статуса
        self.status_label = QLabel("Инициализация...")
        layout.addWidget(self.status_label)
        
        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(max_value)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v из %m (%p%)")
        self.progress_bar.setMinimumHeight(28)
        layout.addWidget(self.progress_bar)
        
        # Информация о времени
        self.time_label = QLabel("")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(9)
        self.time_label.setFont(font)
        layout.addWidget(self.time_label)
        
        # Кнопка отмены
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Отменить расчет")
        self.cancel_button.setMinimumWidth(150)
        self.cancel_button.setMinimumHeight(32)
        self.cancel_button.clicked.connect(self.on_cancel)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def set_status(self, text):
        """Обновить текст статуса"""
        self.status_label.setText(text)
        
    def set_progress(self, value):
        """Обновить значение прогресс-бара"""
        self.progress_bar.setValue(value)
        
    def set_time_info(self, text):
        """Обновить информацию о времени"""
        self.time_label.setText(text)
        
    def set_range(self, min_val, max_val):
        """Установить диапазон прогресс-бара"""
        self.progress_bar.setMinimum(min_val)
        self.progress_bar.setMaximum(max_val)
        
    def set_worker(self, worker):
        """Установить worker для отмены"""
        self.worker = worker
        
    def on_cancel(self):
        """Обработка нажатия кнопки отмены"""
        if self.is_canceled:
            return
            
        self.is_canceled = True
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText("Отменяется...")
        self.status_label.setText("Отмена вычислений...")
        
        if self.worker:
            self.worker.cancel()
        
    def closeEvent(self, event):
        """Переопределение закрытия окна для отмены операции"""
        if not self.is_canceled and self.worker:
            self.on_cancel()
        event.accept()