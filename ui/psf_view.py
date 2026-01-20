import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QComboBox, QLabel, QCheckBox, QGroupBox, QSizePolicy
)
from PyQt6.QtCore import Qt
import pyqtgraph as pg

class PSFView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.in_microns = False
        self.psf_data = None
        self.step_microns = 0.0
        
        self._init_ui()
        
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Панель управления
        control_layout = QHBoxLayout()
        
        control_layout.addWidget(QLabel("Единицы измерения:"))
        self.units_combo = QComboBox()
        self.units_combo.addItems(["Пиксели", "Микроны"])
        self.units_combo.currentIndexChanged.connect(self._on_units_changed)
        control_layout.addWidget(self.units_combo)
        
        self.log_scale_check = QCheckBox("Логарифмическая шкала")
        self.log_scale_check.stateChanged.connect(self._on_log_scale_changed)
        control_layout.addWidget(self.log_scale_check)
        
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
        
        # Основной splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Левая панель - сечения (вертикальный layout)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # График сечения X
        self.x_plot = pg.PlotWidget()
        self.x_plot.setTitle("Сечение по X", color='w', size='12pt')
        self.x_plot.setLabel('left', 'Интенсивность')
        self.x_plot.setLabel('bottom', 'X координата')
        self.x_plot.showGrid(x=True, y=True, alpha=0.3)
        self.x_plot.setBackground('k')
        left_layout.addWidget(self.x_plot)
        
        # График сечения Y
        self.y_plot = pg.PlotWidget()
        self.y_plot.setTitle("Сечение по Y", color='w', size='12pt')
        self.y_plot.setLabel('left', 'Интенсивность')
        self.y_plot.setLabel('bottom', 'Y координата')
        self.y_plot.showGrid(x=True, y=True, alpha=0.3)
        self.y_plot.setBackground('k')
        left_layout.addWidget(self.y_plot)
        
        # Правая панель - изображение
        image_group = QGroupBox("Полутоновое изображение ФРТ")
        image_layout = QVBoxLayout(image_group)
        
        # Создаем PlotWidget для изображения
        self.image_plot = pg.PlotWidget()
        self.image_plot.setAspectLocked(True)
        self.image_plot.setBackground('k')
        self.image_plot.hideAxis('left')
        self.image_plot.hideAxis('bottom')
        
        # Создаем ImageItem
        self.image_item = pg.ImageItem()
        self.image_plot.addItem(self.image_item)
        
        # Добавляем цветовую карту
        colors = [
            (0, 0, 0),
            (45, 5, 61),
            (84, 42, 55),
            (150, 87, 60),
            (208, 171, 141),
            (255, 255, 255)
        ]
        self.cmap = pg.ColorMap(pos=np.linspace(0.0, 1.0, 6), color=colors)
        self.image_item.setColorMap(self.cmap)
        
        # Добавляем цветовую шкалу
        self.colorbar = pg.ColorBarItem(
            values=(0, 1), 
            colorMap=self.cmap,
            label='Интенсивность'
        )
        self.colorbar.setImageItem(self.image_item)
        
        image_layout.addWidget(self.image_plot)
        
        # Добавляем виджеты в splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(image_group)
        splitter.setSizes([400, 600])
        
        # Подключаем сигнал изменения размера splitter
        splitter.splitterMoved.connect(self._on_splitter_moved)
        
        main_layout.addWidget(splitter)
        
    def _on_splitter_moved(self, pos, index):
        """Обработчик изменения размера splitter"""
        if self.psf_data is not None:
            self._update_image_display()
            
    def _on_units_changed(self, index):
        """Обработчик изменения единиц измерения"""
        self.in_microns = (index == 1)
        if self.psf_data is not None:
            self.show_psf(self.psf_data, self.step_microns)
            
    def _on_log_scale_changed(self, state):
        """Обработчик изменения логарифмической шкалы"""
        if self.psf_data is not None:
            self.show_psf(self.psf_data, self.step_microns)
            
    def show_psf(self, psf: np.ndarray, step_microns: float = 0.0):
        """Отобразить PSF и сечения"""
        self.psf_data = psf
        self.step_microns = step_microns
        
        size = psf.shape[0]
        center = size // 2
        
        # Получаем сечения
        x_slice = psf[center, :]
        y_slice = psf[:, center]
        
        # Обновляем сечения
        self._update_slices(x_slice, y_slice, size)
        
        # Обновляем изображение
        self._update_image_display()
        
    def _update_slices(self, x_slice, y_slice, size):
        """Обновить графики сечений"""
        center = size // 2
        
        # Вычисляем координаты
        if self.in_microns and self.step_microns > 0:
            extent = size * self.step_microns / 2
            x_coords = np.linspace(-extent, extent, size)
            y_coords = np.linspace(-extent, extent, size)
            x_label = "X, мкм"
            y_label = "Y, мкм"
        else:
            x_coords = np.arange(size) - center
            y_coords = np.arange(size) - center
            x_label = "X, пиксели"
            y_label = "Y, пиксели"
        
        # Обновляем график сечения X
        self.x_plot.clear()
        self.x_plot.plot(x_coords, x_slice, pen=pg.mkPen(color='b', width=2))
        self.x_plot.setLabel('bottom', x_label)
        
        # Обновляем график сечения Y
        self.y_plot.clear()
        self.y_plot.plot(y_coords, y_slice, pen=pg.mkPen(color='r', width=2))
        self.y_plot.setLabel('bottom', y_label)
        
    def _update_image_display(self):
        """Обновить отображение изображения"""
        if self.psf_data is None:
            return
            
        # Применяем логарифмическую шкалу если нужно
        if self.log_scale_check.isChecked():
            data_to_show = np.log10(self.psf_data + 1e-10)
        else:
            data_to_show = self.psf_data
            
        # Обновляем изображение
        self.image_item.setImage(data_to_show.T)
        
        # Автоматическое масштабирование уровней
        self.image_item.setLevels([data_to_show.min(), data_to_show.max()])
        
        # Устанавливаем правильный масштаб
        size = self.psf_data.shape[0]
        if self.in_microns and self.step_microns > 0:
            extent = size * self.step_microns / 2
            self.image_item.setRect([-extent, -extent, 2*extent, 2*extent])
            
            # Обновляем подписи осей
            self.image_plot.setLabel('bottom', 'X, мкм')
            self.image_plot.setLabel('left', 'Y, мкм')
            
            # Добавляем сетку с физическим масштабом
            self.image_plot.showGrid(x=True, y=True, alpha=0.3)
        else:
            self.image_item.setRect([-size//2, -size//2, size, size])
            
            # Обновляем подписи осей
            self.image_plot.setLabel('bottom', 'X, пиксели')
            self.image_plot.setLabel('left', 'Y, пиксели')
            self.image_plot.showGrid(x=True, y=True, alpha=0.3)