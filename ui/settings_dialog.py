from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QDoubleSpinBox, QGroupBox, QPushButton,
    QGridLayout, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from core.psf_params import ParamPSF


class SettingsDialog(QDialog):
    """Диалог для настройки исходных параметров"""
    
    settings_changed = pyqtSignal(ParamPSF)
    
    def __init__(self, params: ParamPSF = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройка исходных параметров")
        self.setModal(True)
        self.resize(600, 400)
        
        self.params = params if params else ParamPSF()
        self._init_ui()
        self._update_widget_states()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Группа выбора исходного параметра
        param_group = QGroupBox("Исходный параметр для вычислений")
        param_layout = QGridLayout(param_group)
        
        param_layout.addWidget(QLabel("Исходный параметр:"), 0, 0)
        self.param_combo = QComboBox()
        self.param_combo.addItems([
            "Охват зрачка [к.ед.]",
            "Шаг по зрачку [к.ед.]",
            "Шаг по предмету [к.ед.]",
            "Шаг по изображению [к.ед.]"
        ])
        self.param_combo.currentIndexChanged.connect(self._on_param_changed)
        param_layout.addWidget(self.param_combo, 0, 1)
        
        layout.addWidget(param_group)
        
        # Группа параметров
        values_group = QGroupBox("Значения параметров")
        values_layout = QGridLayout(values_group)
        
        # Охват зрачка
        values_layout.addWidget(QLabel("Охват зрачка (к.ед.):"), 0, 0)
        self.pupil_diameter_spin = QDoubleSpinBox()
        self.pupil_diameter_spin.setRange(0.1, 100.0)
        self.pupil_diameter_spin.setSingleStep(0.1)
        self.pupil_diameter_spin.setDecimals(3)
        self.pupil_diameter_spin.setValue(self.params.pupil_diameter)
        self.pupil_diameter_spin.valueChanged.connect(self._on_pupil_diameter_changed)
        values_layout.addWidget(self.pupil_diameter_spin, 0, 1)
        
        values_layout.addWidget(QLabel("Шаг по зрачку (к.ед.):"), 1, 0)
        self.step_pupil_spin = QDoubleSpinBox()
        self.step_pupil_spin.setRange(0.001, 10.0)
        self.step_pupil_spin.setSingleStep(0.001)
        self.step_pupil_spin.setDecimals(6)
        self.step_pupil_spin.setValue(self.params.step_pupil)
        self.step_pupil_spin.valueChanged.connect(self._on_step_pupil_changed)
        values_layout.addWidget(self.step_pupil_spin, 1, 1)
        
        values_layout.addWidget(QLabel("Шаг по предмету (к.ед.):"), 2, 0)
        self.step_object_spin = QDoubleSpinBox()
        self.step_object_spin.setRange(0.001, 10.0)
        self.step_object_spin.setSingleStep(0.001)
        self.step_object_spin.setDecimals(6)
        self.step_object_spin.setValue(self.params.step_object)
        self.step_object_spin.valueChanged.connect(self._on_step_object_changed)
        values_layout.addWidget(self.step_object_spin, 2, 1)
        
        values_layout.addWidget(QLabel("Шаг по изображению (к.ед.):"), 3, 0)
        self.step_image_spin = QDoubleSpinBox()
        self.step_image_spin.setRange(0.001, 10.0)
        self.step_image_spin.setSingleStep(0.001)
        self.step_image_spin.setDecimals(6)
        self.step_image_spin.setValue(self.params.step_image)
        self.step_image_spin.valueChanged.connect(self._on_step_image_changed)
        values_layout.addWidget(self.step_image_spin, 3, 1)
        
        # Размер (количество точек)
        values_layout.addWidget(QLabel("Размер (точек):"), 4, 0)
        self.size_spin = QDoubleSpinBox()
        self.size_spin.setRange(32, 4096)
        self.size_spin.setSingleStep(32)
        self.size_spin.setValue(self.params.size)
        self.size_spin.valueChanged.connect(self._on_size_changed)
        values_layout.addWidget(self.size_spin, 4, 1)
        
        values_layout.setColumnStretch(1, 1)
        layout.addWidget(values_group)
        
        # Группа единиц измерения
        units_group = QGroupBox("Единицы измерения")
        units_layout = QGridLayout(units_group)
        
        units_layout.addWidget(QLabel("Шаг в изображении (мкм):"), 0, 0)
        self.step_microns_label = QLabel("0.000")
        self.step_microns_label.setStyleSheet("font-weight: bold; padding: 5px; border: 1px solid #ccc;")
        units_layout.addWidget(self.step_microns_label, 0, 1)
        
        layout.addWidget(units_group)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        self.calculate_button = QPushButton("Пересчитать")
        self.calculate_button.clicked.connect(self._recalculate_all)
        
        self.apply_button = QPushButton("Применить")
        self.apply_button.clicked.connect(self._apply_changes)
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self._ok_clicked)
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.calculate_button)
        button_layout.addStretch()
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
    def _update_widget_states(self):
        """Обновить состояние виджетов в зависимости от выбранного параметра"""
        param_idx = self.param_combo.currentIndex()
        
        # Все виджеты изначально доступны
        self.pupil_diameter_spin.setEnabled(True)
        self.step_pupil_spin.setEnabled(True)
        self.step_object_spin.setEnabled(True)
        self.step_image_spin.setEnabled(True)
        self.size_spin.setEnabled(True)
        
        # Делаем доступным только выбранный параметр
        if param_idx == 0:  # Охват зрачка
            self.step_pupil_spin.setEnabled(False)
            self.step_object_spin.setEnabled(False)
            self.step_image_spin.setEnabled(False)
        elif param_idx == 1:  # Шаг по зрачку
            self.pupil_diameter_spin.setEnabled(False)
            self.step_object_spin.setEnabled(False)
            self.step_image_spin.setEnabled(False)
        elif param_idx == 2:  # Шаг по предмету
            self.pupil_diameter_spin.setEnabled(False)
            self.step_pupil_spin.setEnabled(False)
            self.step_image_spin.setEnabled(False)
        elif param_idx == 3:  # Шаг по изображению
            self.pupil_diameter_spin.setEnabled(False)
            self.step_pupil_spin.setEnabled(False)
            self.step_object_spin.setEnabled(False)
            
    def _on_param_changed(self, index):
        """Обработчик изменения выбранного параметра"""
        self._update_widget_states()
        self._recalculate_all()
        
    def _on_pupil_diameter_changed(self, value):
        """Обработчик изменения охвата зрачка"""
        if self.param_combo.currentIndex() == 0:  # Охват зрачка выбран как исходный
            if self.params.size > 0:
                self.params.pupil_diameter = value
                self.params.step_pupil = value / self.params.size
                self._update_step_params()
                self._update_display()
                
    def _on_step_pupil_changed(self, value):
        """Обработчик изменения шага по зрачку"""
        if self.param_combo.currentIndex() == 1:  # Шаг по зрачку выбран как исходный
            if value > 0:
                self.params.step_pupil = value
                self.params.pupil_diameter = value * self.params.size
                self._update_step_params()
                self._update_display()
                
    def _on_step_object_changed(self, value):
        """Обработчик изменения шага по предмету"""
        if self.param_combo.currentIndex() == 2:  # Шаг по предмету выбран как исходный
            if value > 0:
                self.params.step_object = value
                self.params.step_image = value
                if value > 0 and self.params.size > 0:
                    self.params.step_pupil = 1.0 / (value * self.params.size)
                    self.params.pupil_diameter = self.params.step_pupil * self.params.size
                self._update_display()
                
    def _on_step_image_changed(self, value):
        """Обработчик изменения шага по изображению"""
        if self.param_combo.currentIndex() == 3:  # Шаг по изображению выбран как исходный
            if value > 0:
                self.params.step_image = value
                self.params.step_object = value
                if value > 0 and self.params.size > 0:
                    self.params.step_pupil = 1.0 / (value * self.params.size)
                    self.params.pupil_diameter = self.params.step_pupil * self.params.size
                self._update_display()
                
    def _on_size_changed(self, value):
        """Обработчик изменения размера"""
        self.params.size = int(value)
        self._recalculate_all()
        
    def _update_step_params(self):
        """Обновить параметры шагов на основе текущих значений"""
        if self.params.step_pupil > 0 and self.params.size > 0:
            self.params.step_object = 1.0 / (self.params.step_pupil * self.params.size)
            self.params.step_image = self.params.step_object
            
    def _update_display(self):
        """Обновить отображение значений"""
        # Блокируем сигналы чтобы избежать рекурсии
        self.pupil_diameter_spin.blockSignals(True)
        self.step_pupil_spin.blockSignals(True)
        self.step_object_spin.blockSignals(True)
        self.step_image_spin.blockSignals(True)
        self.size_spin.blockSignals(True)
        
        # Обновляем значения
        self.pupil_diameter_spin.setValue(self.params.pupil_diameter)
        self.step_pupil_spin.setValue(self.params.step_pupil)
        self.step_object_spin.setValue(self.params.step_object)
        self.step_image_spin.setValue(self.params.step_image)
        self.size_spin.setValue(self.params.size)
        
        # Вычисляем шаг в микронах
        if self.params.step_image > 0 and self.params.wavelength > 0:
            step_microns = self.params.step_object * self.params.wavelength / \
                          (self.params.magnification * self.params.back_aperture)
            self.step_microns_label.setText(f"{step_microns:.6f}")
        
        # Разблокируем сигналы
        self.pupil_diameter_spin.blockSignals(False)
        self.step_pupil_spin.blockSignals(False)
        self.step_object_spin.blockSignals(False)
        self.step_image_spin.blockSignals(False)
        self.size_spin.blockSignals(False)
        
    def _recalculate_all(self):
        """Пересчитать все параметры"""
        param_idx = self.param_combo.currentIndex()
        
        if param_idx == 0:  # Охват зрачка
            if self.params.size > 0:
                self.params.step_pupil = self.params.pupil_diameter / self.params.size
                self._update_step_params()
                
        elif param_idx == 1:  # Шаг по зрачку
            if self.params.step_pupil > 0:
                self.params.pupil_diameter = self.params.step_pupil * self.params.size
                self._update_step_params()
                
        elif param_idx == 2:  # Шаг по предмету
            if self.params.step_object > 0 and self.params.size > 0:
                self.params.step_image = self.params.step_object
                self.params.step_pupil = 1.0 / (self.params.step_object * self.params.size)
                self.params.pupil_diameter = self.params.step_pupil * self.params.size
                
        elif param_idx == 3:  # Шаг по изображению
            if self.params.step_image > 0 and self.params.size > 0:
                self.params.step_object = self.params.step_image
                self.params.step_pupil = 1.0 / (self.params.step_image * self.params.size)
                self.params.pupil_diameter = self.params.step_pupil * self.params.size
                
        self._update_display()
        
    def _apply_changes(self):
        """Применить изменения"""
        self.settings_changed.emit(self.params)
        
    def _ok_clicked(self):
        """Обработчик кнопки OK"""
        self._apply_changes()
        self.accept()
        
    def get_params(self) -> ParamPSF:
        """Получить текущие параметры"""
        return self.params
        
    def set_params(self, params: ParamPSF):
        """Установить параметры"""
        self.params = params
        self._update_display()
        self._recalculate_all()