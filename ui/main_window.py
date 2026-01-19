from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QGridLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QGroupBox, QFileDialog, QMessageBox, QToolBar,
    QVBoxLayout, QHBoxLayout, QSplitter
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from core.psf_params import ParamPSF
from core.psf_calculator import PSFCalculator
from ui.psf_view import PSFView
from ui.log_widget import LogWidget
import json
import numpy as np

class PSFMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вычисление ФРТ")
        self.resize(1400, 800)

        self.params = ParamPSF()
        self.calculator = PSFCalculator()
        self.current_psf = None
        self.strehl_ratio = 0.0

        self._init_ui()
        self._init_menu_toolbar()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        
        # Верхняя панель с параметрами
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        
        # ===== Левый блок - параметры системы =====
        sys_box = QGroupBox("Параметры оптической системы")
        sys_layout = QGridLayout(sys_box)
        
        self.ed_lambda = QLineEdit(str(self.params.wavelength))
        self.ed_aperture = QLineEdit(str(self.params.back_aperture))
        self.ed_mag = QLineEdit(str(self.params.magnification))
        self.ed_defocus = QLineEdit(str(self.params.defocus))
        self.ed_astig = QLineEdit(str(self.params.astigmatism))
        
        sys_layout.addWidget(QLabel("Длина волны, мкм"), 0, 0)
        sys_layout.addWidget(self.ed_lambda, 0, 1)
        sys_layout.addWidget(QLabel("Задняя апертура"), 1, 0)
        sys_layout.addWidget(self.ed_aperture, 1, 1)
        sys_layout.addWidget(QLabel("Увеличение"), 2, 0)
        sys_layout.addWidget(self.ed_mag, 2, 1)
        sys_layout.addWidget(QLabel("Расфокусировка"), 3, 0)
        sys_layout.addWidget(self.ed_defocus, 3, 1)
        sys_layout.addWidget(QLabel("Астигматизм"), 4, 0)
        sys_layout.addWidget(self.ed_astig, 4, 1)
        
        # ===== Правый блок - численные параметры =====
        num_box = QGroupBox("Численные параметры")
        num_layout = QGridLayout(num_box)
        
        self.cb_size = QComboBox()
        self.cb_size.addItems(["128", "256", "512", "1024", "2048"])
        self.cb_size.setCurrentText("512")
        
        self.cb_source = QComboBox()
        self.cb_source.addItems([
            "Охват зрачка [к.ед.]",
            "Шаг по зрачку [к.ед.]",
            "Шаг по предмету/изображению [к.ед.]"
        ])
        
        self.ed_pupil = QLineEdit(str(self.params.pupil_diameter))
        self.ed_step_pupil = QLineEdit(str(self.params.step_pupil))
        self.ed_step_obj = QLineEdit(str(self.params.step_object))
        
        num_layout.addWidget(QLabel("Размер выборки"), 0, 0)
        num_layout.addWidget(self.cb_size, 0, 1)
        num_layout.addWidget(QLabel("Исходный параметр"), 1, 0)
        num_layout.addWidget(self.cb_source, 1, 1)
        
        num_layout.addWidget(QLabel("Охват зрачка"), 2, 0)
        num_layout.addWidget(self.ed_pupil, 2, 1)
        num_layout.addWidget(QLabel("Шаг по зрачку"), 3, 0)
        num_layout.addWidget(self.ed_step_pupil, 3, 1)
        num_layout.addWidget(QLabel("Шаг по предмету"), 4, 0)
        num_layout.addWidget(self.ed_step_obj, 4, 1)
        
        # Добавляем блоки в верхнюю панель
        top_layout.addWidget(sys_box)
        top_layout.addWidget(num_box)
        
        main_layout.addWidget(top_widget)
        
        # ===== Кнопки =====
        button_layout = QHBoxLayout()
        
        self.btn_calc = QPushButton("Рассчитать ФРТ")
        self.btn_calc.setMinimumHeight(40)
        self.btn_calc.clicked.connect(self._calculate)
        
        self.btn_export = QPushButton("Экспорт данных")
        self.btn_export.setMinimumHeight(40)
        self.btn_export.clicked.connect(self._export_data)
        
        button_layout.addWidget(self.btn_calc)
        button_layout.addWidget(self.btn_export)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # ===== Центральный splitter =====
        center_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Верхняя часть - графики
        self.psf_view = PSFView()
        center_splitter.addWidget(self.psf_view)
        
        # Нижняя часть - лог
        self.log_widget = LogWidget()
        center_splitter.addWidget(self.log_widget)
        
        center_splitter.setSizes([600, 200])
        main_layout.addWidget(center_splitter)
        
        # Подключаем сигналы
        self.cb_source.currentIndexChanged.connect(self._update_source_mode)
        self._update_source_mode()
        
    def _init_menu_toolbar(self):
        menu = self.menuBar()
        
        # Меню Файл
        file_menu = menu.addMenu("Файл")
        
        act_load = QAction("Загрузить параметры", self)
        act_save = QAction("Сохранить параметры", self)
        act_reset = QAction("Сбросить параметры", self)
        act_export = QAction("Экспорт изображения", self)
        act_exit = QAction("Выход", self)
        
        act_load.triggered.connect(self.load_params)
        act_save.triggered.connect(self.save_params)
        act_reset.triggered.connect(self.reset_params)
        act_export.triggered.connect(self._export_image)
        act_exit.triggered.connect(self.close)
        
        file_menu.addAction(act_load)
        file_menu.addAction(act_save)
        file_menu.addAction(act_reset)
        file_menu.addSeparator()
        file_menu.addAction(act_export)
        file_menu.addSeparator()
        file_menu.addAction(act_exit)
        
        # Toolbar
        toolbar = QToolBar("Основные действия")
        self.addToolBar(toolbar)
        
        toolbar.addAction(act_load)
        toolbar.addAction(act_save)
        toolbar.addAction(act_reset)
        toolbar.addSeparator()
        toolbar.addAction(act_export)
        
    def _update_source_mode(self):
        idx = self.cb_source.currentIndex()
        self.ed_pupil.setEnabled(idx == 0)
        self.ed_step_pupil.setEnabled(idx == 1)
        self.ed_step_obj.setEnabled(idx == 2)
        
    def _calculate(self):
        try:
            # Получаем параметры из UI
            self.params.size = int(self.cb_size.currentText())
            self.params.wavelength = float(self.ed_lambda.text())
            self.params.back_aperture = float(self.ed_aperture.text())
            self.params.magnification = float(self.ed_mag.text())
            self.params.defocus = float(self.ed_defocus.text())
            self.params.astigmatism = float(self.ed_astig.text())
            self.params.pupil_diameter = float(self.ed_pupil.text())
            self.params.step_pupil = float(self.ed_step_pupil.text())
            self.params.step_object = float(self.ed_step_obj.text())
            
            # Вычисляем PSF
            self.current_psf, self.strehl_ratio = self.calculator.compute(self.params)
            
            # Получаем шаг в микронах
            step_microns = self.calculator._step_im_microns
            
            # Отображаем результаты
            self.psf_view.show_psf(self.current_psf, step_microns)
            
            # Записываем в лог
            self._log_calculation_results()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            self.log_widget.add_log(f"Ошибка: {str(e)}")
            
    def _log_calculation_results(self):
        """Записать результаты вычисления в лог"""
        self.log_widget.clear_log()
        self.log_widget.log_params(self.params)
        self.log_widget.add_log("=== Результаты вычисления ===")
        self.log_widget.add_log(f"Число Штреля: {self.strehl_ratio:.6f}")
        self.log_widget.add_log(f"Максимум интенсивности: {np.max(self.current_psf):.6f}")
        self.log_widget.add_log(f"Минимум интенсивности: {np.min(self.current_psf):.6f}")
        self.log_widget.add_log(f"Сумма интенсивности: {np.sum(self.current_psf):.6f}")
        self.log_widget.add_log(f"Шаг в изображении: {self.calculator._step_im_microns:.6f} мкм")
        
    def _export_data(self):
        """Экспорт данных PSF в файл"""
        if self.current_psf is None:
            QMessageBox.warning(self, "Предупреждение", "Сначала рассчитайте ФРТ")
            return
            
        path, _ = QFileDialog.getSaveFileName(
            self, 
            "Экспорт данных", 
            "", 
            "NumPy Files (*.npy);;Text Files (*.txt);;All Files (*)"
        )
        
        if path:
            try:
                if path.endswith('.npy'):
                    np.save(path, self.current_psf)
                else:
                    np.savetxt(path, self.current_psf)
                    
                self.log_widget.add_log(f"Данные экспортированы в: {path}")
                QMessageBox.information(self, "Успех", "Данные успешно экспортированы")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка экспорта", str(e))
                
    def _export_image(self):
        """Экспорт изображения PSF"""
        if self.current_psf is None:
            QMessageBox.warning(self, "Предупреждение", "Сначала рассчитайте ФРТ")
            return
            
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт изображения",
            "",
            "PNG Images (*.png);;JPEG Images (*.jpg *.jpeg);;All Files (*)"
        )
        
        if path:
            try:
                import matplotlib.pyplot as plt
                
                # Создаем изображение с цветовой картой
                plt.figure(figsize=(8, 8))
                plt.imshow(self.current_psf, cmap='inferno')
                plt.colorbar(label='Интенсивность')
                plt.title(f'PSF (Strehl ratio: {self.strehl_ratio:.4f})')
                plt.savefig(path, dpi=300, bbox_inches='tight')
                plt.close()
                
                self.log_widget.add_log(f"Изображение экспортировано в: {path}")
                QMessageBox.information(self, "Успех", "Изображение успешно экспортировано")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка экспорта", str(e))
                
    def load_params(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 
            "Открыть параметры", 
            "", 
            "JSON Files (*.json);;All Files (*)"
        )
        
        if path:
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    
                # Обновляем параметры
                for key, value in data.items():
                    if hasattr(self.params, key):
                        setattr(self.params, key, value)
                        
                # Обновляем UI
                self._update_ui_from_params()
                
                self.log_widget.add_log(f"Параметры загружены из: {path}")
                QMessageBox.information(self, "Успех", "Параметры успешно загружены")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка загрузки", str(e))
                self.log_widget.add_log(f"Ошибка загрузки параметров: {str(e)}")
                
    def save_params(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить параметры",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if path:
            try:
                if not path.endswith('.json'):
                    path += '.json'
                    
                data = self.params.__dict__
                with open(path, "w") as f:
                    json.dump(data, f, indent=4)
                    
                self.log_widget.add_log(f"Параметры сохранены в: {path}")
                QMessageBox.information(self, "Успех", "Параметры успешно сохранены")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка сохранения", str(e))
                self.log_widget.add_log(f"Ошибка сохранения параметров: {str(e)}")
                
    def reset_params(self):
        reply = QMessageBox.question(
            self,
            "Сброс параметров",
            "Вы уверены, что хотите сбросить все параметры к значениям по умолчанию?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.params = ParamPSF()
            self._update_ui_from_params()
            self.log_widget.add_log("Параметры сброшены к значениям по умолчанию")
            
    def _update_ui_from_params(self):
        self.ed_lambda.setText(str(self.params.wavelength))
        self.ed_aperture.setText(str(self.params.back_aperture))
        self.ed_mag.setText(str(self.params.magnification))
        self.ed_defocus.setText(str(self.params.defocus))
        self.ed_astig.setText(str(self.params.astigmatism))
        self.ed_pupil.setText(str(self.params.pupil_diameter))
        self.ed_step_pupil.setText(str(self.params.step_pupil))
        self.ed_step_obj.setText(str(self.params.step_object))
        
        # Устанавливаем размер
        index = self.cb_size.findText(str(self.params.size))
        if index >= 0:
            self.cb_size.setCurrentIndex(index)