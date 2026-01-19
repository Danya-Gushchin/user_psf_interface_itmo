from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QGridLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QGroupBox, QFileDialog, QMessageBox, QToolBar
)
from PyQt6.QtGui import QAction
from core.psf_params import ParamPSF
from core.psf_calculator import PSFCalculator
from ui.psf_view import PSFView
import json


class PSFMainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вычисление ФРТ")

        self.params = ParamPSF()
        self.calculator = PSFCalculator()

        self._init_ui()
        self._init_menu_toolbar()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QGridLayout(central)

        # ===== Параметры системы =====
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

        # ===== Численные параметры =====
        num_box = QGroupBox("Численные параметры")
        num_layout = QGridLayout(num_box)

        self.cb_size = QComboBox()
        self.cb_size.addItems(["128", "256", "512", "1024", "2048"])

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

        # ===== Кнопка =====
        self.btn_calc = QPushButton("Рассчитать ФРТ")

        # ===== Окно отображения =====
        self.psf_view = PSFView(self)

        # ===== Layout =====
        layout.addWidget(sys_box, 0, 0)
        layout.addWidget(num_box, 0, 1)
        layout.addWidget(self.btn_calc, 1, 1)
        layout.addWidget(self.psf_view, 0, 2, 2, 1)

        self.cb_source.currentIndexChanged.connect(self._update_source_mode)
        self.btn_calc.clicked.connect(self._calculate)
        self._update_source_mode()

    def _init_menu_toolbar(self):
        # ===== Menu =====
        menu = self.menuBar()
        file_menu = menu.addMenu("Файл")

        act_load = QAction("Прочитать", self)
        act_save = QAction("Сохранить", self)
        act_reset = QAction("Сбросить по умолчанию", self)

        act_load.triggered.connect(self.load_params)
        act_save.triggered.connect(self.save_params)
        act_reset.triggered.connect(self.reset_params)

        file_menu.addAction(act_load)
        file_menu.addAction(act_save)
        file_menu.addAction(act_reset)

        # ===== Toolbar =====
        toolbar = QToolBar("Основные действия")
        self.addToolBar(toolbar)
        toolbar.addAction(act_load)
        toolbar.addAction(act_save)
        toolbar.addAction(act_reset)

    def _update_source_mode(self):
        idx = self.cb_source.currentIndex()
        self.ed_pupil.setEnabled(idx == 0)
        self.ed_step_pupil.setEnabled(idx == 1)
        self.ed_step_obj.setEnabled(idx == 2)

    def _calculate(self):
        try:
            self.params.size = int(self.cb_size.currentText())
            self.params.wavelength = float(self.ed_lambda.text())
            self.params.back_aperture = float(self.ed_aperture.text())
            self.params.magnification = float(self.ed_mag.text())
            self.params.defocus = float(self.ed_defocus.text())
            self.params.astigmatism = float(self.ed_astig.text())
            self.params.pupil_diameter = float(self.ed_pupil.text())
            self.params.step_pupil = float(self.ed_step_pupil.text())
            self.params.step_object = float(self.ed_step_obj.text())

            psf = self.calculator.compute(self.params)
            self.psf_view.show_psf(psf)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def load_params(self):
        path, _ = QFileDialog.getOpenFileName(self, "Открыть параметры", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                for key, value in data.items():
                    if hasattr(self.params, key):
                        setattr(self.params, key, value)
                self._update_ui_from_params()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка загрузки", str(e))

    def save_params(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить параметры", "", "JSON Files (*.json)")
        if path:
            try:
                data = self.params.__dict__
                with open(path, "w") as f:
                    json.dump(data, f, indent=4)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка сохранения", str(e))

    def reset_params(self):
        self.params = ParamPSF()
        self._update_ui_from_params()

    def _update_ui_from_params(self):
        self.ed_lambda.setText(str(self.params.wavelength))
        self.ed_aperture.setText(str(self.params.back_aperture))
        self.ed_mag.setText(str(self.params.magnification))
        self.ed_defocus.setText(str(self.params.defocus))
        self.ed_astig.setText(str(self.params.astigmatism))
        self.ed_pupil.setText(str(self.params.pupil_diameter))
        self.ed_step_pupil.setText(str(self.params.step_pupil))
        self.ed_step_obj.setText(str(self.params.step_object))
