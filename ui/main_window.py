from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QGridLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QGroupBox, QFileDialog, QMessageBox, QToolBar,
    QVBoxLayout, QHBoxLayout, QSplitter, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QSpinBox, QDoubleSpinBox, QCheckBox,
    QApplication, QMenu, QAbstractItemView, QDockWidget, QDialog
)
from PyQt6.QtGui import QAction, QClipboard, QKeySequence
from PyQt6.QtCore import Qt, pyqtSignal
from core.psf_params import ParamPSF
from core.psf_calculator import PSFCalculator
from ui.psf_view import PSFView
from ui.log_widget import LogWidget
from ui.settings_dialog import SettingsDialog
import json
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import io
import traceback
import pandas as pd
import csv
from ui.report_generator import ReportGenerator
from ui.preview_dialog import PreviewDialog


class ParameterTable(QTableWidget):
    """Таблица параметров с вычислением числа Штреля"""
    
    calculation_complete = pyqtSignal(int, float)  # row, strehl_ratio
    selection_changed = pyqtSignal(int)  # row
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.calculator = PSFCalculator()
        self.current_params_list = []
        
        self._init_table()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
    def _init_table(self):
        """Инициализация таблицы"""
        headers = [
            "№", "Размер", "λ (мкм)", "Апертура", "Ув.", 
            "Расфок.", "Астигм.", 
            "Охват зр.",   # Охват зрачка (к.ед.)
            "Шаг зр.",     # Шаг по зрачку (к.ед.)
            "Шаг предм.",  # Шаг по предмету (к.ед.)
            "Шаг изобр.",  # Шаг по изображению (к.ед.)
            "Штрель", 
            "Статус"
        ]
        
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # Настраиваем размеры колонок
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.setColumnWidth(0, 40)   # №
        self.setColumnWidth(1, 60)   # Размер
        self.setColumnWidth(2, 70)   # λ
        self.setColumnWidth(3, 80)   # Апертура
        self.setColumnWidth(4, 50)   # Ув.
        self.setColumnWidth(5, 70)   # Расфок.
        self.setColumnWidth(6, 70)   # Астигм.
        self.setColumnWidth(7, 70)   # Охват зрачка (к.ед.)
        self.setColumnWidth(8, 70)   # Шаг по зрачку (к.ед.)
        self.setColumnWidth(9, 70)   # Шаг по предмету (к.ед.)
        self.setColumnWidth(10, 70)  # Шаг по изображению (к.ед.)
        self.setColumnWidth(11, 80)  # Штрель
        self.setColumnWidth(12, 100) # Статус
        
        # Настраиваем выбор строк
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Подключаем сигнал выбора
        self.itemSelectionChanged.connect(self._on_selection_changed)
    
    def get_selected_rows(self):
        """Получить список выбранных строк"""
        try:
            # Способ 1: через selectionModel
            indexes = self.selectionModel().selectedRows()
            if indexes:
                return [index.row() for index in indexes]
            
            # Способ 2: через selectedItems
            selected_items = self.selectedItems()
            if selected_items:
                return sorted(set([item.row() for item in selected_items]))
            
            # Способ 3: через currentRow
            current_row = self.currentRow()
            if current_row >= 0:
                return [current_row]
                
            return []
        except Exception as e:
            print(f"Ошибка в get_selected_rows: {e}")
            return []
    
    def _show_context_menu(self, position):
        """Показать контекстное меню"""
        menu = QMenu()
        
        calc_selected_action = menu.addAction("Вычислить выбранную")
        calc_all_action = menu.addAction("Вычислить все")
        menu.addSeparator()
        add_row_action = menu.addAction("Добавить строку")
        delete_row_action = menu.addAction("Удалить строку")
        clear_table_action = menu.addAction("Очистить таблицу")
        menu.addSeparator()
        copy_action = menu.addAction("Копировать таблицу")
        
        action = menu.exec(self.mapToGlobal(position))
        
        if action == calc_selected_action:
            self.calculate_selected()
        elif action == calc_all_action:
            self.calculate_all()
        elif action == add_row_action:
            self.add_row()
        elif action == delete_row_action:
            self.delete_selected_row()
        elif action == clear_table_action:
            self.clear_table()
        elif action == copy_action:
            self.copy_to_clipboard()
    
    def add_row(self, params: ParamPSF = None):
        """Добавить строку в таблицу"""
        row = self.rowCount()
        self.insertRow(row)
        
        # Заполняем номер
        item = QTableWidgetItem(str(row + 1))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row, 0, item)
        
        # Если переданы параметры, заполняем ими
        if params:
            self._fill_row_with_params(row, params)
        else:
            # Значения по умолчанию
            default_values = [
                "512", "0.555", "0.5", "1.0", 
                "0.0", "0.0", 
                "8.0",       # Охват зрачка
                "0.0625",    # Шаг по зрачку
                "0.13875",   # Шаг по предмету
                "0.13875",   # Шаг по изображению
                "0.000", "Не рассч."
            ]
            
            for col, value in enumerate(default_values, 1):
                item = QTableWidgetItem(value)
                if col in [1, 2, 3, 5, 6, 7, 8, 9, 10, 11]:  # Числовые поля
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                elif col == 12:  # Статус
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setItem(row, col, item)
        
        # Сохраняем параметры
        if params:
            self.current_params_list.append(params)
        else:
            self.current_params_list.append(ParamPSF())
            
    def _fill_row_with_params(self, row: int, params: ParamPSF):
        """Заполнить строку параметрами"""
        values = [
            str(params.size),
            f"{params.wavelength:.3f}",
            f"{params.back_aperture:.3f}",
            f"{params.magnification:.1f}",
            f"{params.defocus:.3f}",
            f"{params.astigmatism:.3f}",
            f"{params.pupil_diameter:.3f}",     # Охват зрачка
            f"{params.step_pupil:.6f}",         # Шаг по зрачку
            f"{params.step_object:.6f}",        # Шаг по предмету
            f"{params.step_image:.6f}",         # Шаг по изображению
            "0.000",
            "Не рассч."
        ]
        
        for col, value in enumerate(values, 1):
            item = QTableWidgetItem(value)
            if col in [1, 2, 3, 5, 6, 7, 8, 9, 10, 11]:  # Числовые поля
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            elif col == 12:  # Статус
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(row, col, item)
    
    def delete_selected_row(self):
        """Удалить выбранную строку"""
        selected = self.get_selected_rows()
        if not selected:
            return
            
        row = selected[0]
        self.removeRow(row)
        
        # Удаляем из списка параметров
        if row < len(self.current_params_list):
            self.current_params_list.pop(row)
            
        # Обновляем номера строк
        self._renumber_rows()
    
    def clear_table(self):
        """Очистить таблицу"""
        self.setRowCount(0)
        self.current_params_list.clear()
    
    def _renumber_rows(self):
        """Перенумеровать строки"""
        for row in range(self.rowCount()):
            self.item(row, 0).setText(str(row + 1))
    
    def calculate_selected(self):
        """Вычислить выбранную строку"""
        selected = self.get_selected_rows()
        if not selected:
            QMessageBox.warning(self, "Предупреждение", "Выберите строку для вычисления")
            return
            
        row = selected[0]
        self._calculate_row(row)
    
    def calculate_all(self):
        """Вычислить все строки"""
        if self.rowCount() == 0:
            return
            
        for row in range(self.rowCount()):
            self._calculate_row(row)
    
    def _calculate_row(self, row: int):
        """Вычислить строку с заданным номером"""
        try:
            # Получаем параметры из таблицы
            params = self._get_params_from_row(row)
            if params is None:
                self.setItem(row, 12, QTableWidgetItem("Ошибка ввода"))
                return
                
            # Вычисляем PSF
            psf, strehl_ratio = self.calculator.compute(params)
            
            # Обновляем таблицу
            item = QTableWidgetItem(f"{strehl_ratio:.6f}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.setItem(row, 11, item)
            
            item = QTableWidgetItem("Рассчитано")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(row, 12, item)
            
            # Сохраняем обновленные параметры
            if row < len(self.current_params_list):
                self.current_params_list[row] = params
            else:
                self.current_params_list.append(params)
                
            # Сигнализируем о завершении расчета
            self.calculation_complete.emit(row, strehl_ratio)
            
        except Exception as e:
            item = QTableWidgetItem("Ошибка")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(row, 12, item)
            print(f"Ошибка вычисления строки {row}: {e}")
            traceback.print_exc()
    
    def _get_params_from_row(self, row: int) -> ParamPSF:
        """Получить параметры из строки таблицы"""
        try:
            params = ParamPSF()
            
            # Получаем значения из ячеек
            cells = {}
            for col in range(1, 11):  # Теперь 10 колонок с данными (до Штреля)
                item = self.item(row, col)
                if item and item.text().strip():
                    cells[col] = item.text().strip()
                else:
                    cells[col] = ""
            
            # Парсим значения с проверкой на пустоту
            params.size = int(cells[1]) if cells[1] else 512
            params.wavelength = float(cells[2]) if cells[2] else 0.555
            params.back_aperture = float(cells[3]) if cells[3] else 0.5
            params.magnification = float(cells[4]) if cells[4] else 1.0
            params.defocus = float(cells[5]) if cells[5] else 0.0
            params.astigmatism = float(cells[6]) if cells[6] else 0.0
            params.pupil_diameter = float(cells[7]) if cells[7] else 8.0
            params.step_pupil = float(cells[8]) if cells[8] else 0.0625
            params.step_object = float(cells[9]) if cells[9] else 0.13875
            params.step_image = float(cells[10]) if cells[10] else 0.13875
            
            return params
            
        except Exception as e:
            print(f"Ошибка парсинга параметров строки {row}: {e}")
            traceback.print_exc()
            return None
    
    def recalculate_steps(self):
        """Пересчитать шаги для всех строк"""
        for row in range(self.rowCount()):
            try:
                params = self._get_params_from_row(row)
                if params:
                    # Пересчитываем параметры дискретизации
                    if params.pupil_diameter > 0 and params.size > 0:
                        params.step_pupil = params.pupil_diameter / params.size
                    
                    if params.step_pupil > 0 and params.size > 0:
                        params.step_object = 1.0 / (params.step_pupil * params.size)
                        params.step_image = params.step_object
                    
                    # Обновляем параметры в списке
                    if row < len(self.current_params_list):
                        self.current_params_list[row] = params
                    
                    # Обновляем отображение в таблице
                    self._update_row_steps(row, params)
                    
            except Exception as e:
                print(f"Ошибка пересчета шагов строки {row}: {e}")
    
    def _update_row_steps(self, row: int, params: ParamPSF):
        """Обновить отображение шагов в строке таблицы"""
        # Обновляем значения шагов в таблице
        step_items = [
            (7, f"{params.pupil_diameter:.3f}"),
            (8, f"{params.step_pupil:.6f}"),
            (9, f"{params.step_object:.6f}"),
            (10, f"{params.step_image:.6f}")
        ]
        
        for col, value in step_items:
            item = self.item(row, col)
            if item:
                item.setText(value)
            else:
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.setItem(row, col, item)
    
    def get_selected_params(self) -> ParamPSF:
        """Получить параметры выбранной строки"""
        selected = self.get_selected_rows()
        if not selected:
            return None
            
        row = selected[0]
        if row < len(self.current_params_list):
            return self.current_params_list[row]
        return self._get_params_from_row(row)
    
    def get_selected_strehl(self) -> float:
        """Получить число Штреля выбранной строки"""
        selected = self.get_selected_rows()
        if not selected:
            return 0.0
            
        row = selected[0]
        item = self.item(row, 11)  # Колонка Штреля
        if item and item.text().strip():
            try:
                return float(item.text())
            except:
                return 0.0
        return 0.0
    
    def _on_selection_changed(self):
        """Обработчик изменения выбора строки"""
        selected = self.get_selected_rows()
        if selected:
            self.selection_changed.emit(selected[0])
    
    def copy_to_clipboard(self):
        """Копировать таблицу в буфер обмена"""
        clipboard = QApplication.clipboard()
        text = self._get_table_as_text()
        clipboard.setText(text)
        QMessageBox.information(self, "Копирование", "Таблица скопирована в буфер обмена")
    
    def _get_table_as_text(self) -> str:
        """Получить таблицу в виде текста"""
        rows = self.rowCount()
        cols = self.columnCount()
        
        if rows == 0:
            return ""
        
        # Получаем заголовки
        headers = []
        for col in range(cols):
            headers.append(self.horizontalHeaderItem(col).text())
        
        # Получаем данные
        data = []
        for row in range(rows):
            row_data = []
            for col in range(cols):
                item = self.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        
        # Формируем текст
        text_lines = ["\t".join(headers)]
        for row in data:
            text_lines.append("\t".join(row))
        
        return "\n".join(text_lines)
    
    def get_table_data(self) -> list:
        """Получить все данные таблицы в виде списка словарей"""
        data = []
        for row in range(self.rowCount()):
            row_data = {}
            for col in range(self.columnCount()):
                header = self.horizontalHeaderItem(col).text()
                item = self.item(row, col)
                row_data[header] = item.text() if item else ""
            data.append(row_data)
        return data
    
    def export_to_file(self, filename: str):
        """Экспортировать таблицу в файл"""
        try:
            # Определяем расширение файла
            if filename.endswith('.csv'):
                delimiter = ','
            else:
                delimiter = '\t'
            
            with open(filename, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f, delimiter=delimiter)
                
                # Записываем заголовки
                headers = []
                for col in range(self.columnCount()):
                    headers.append(self.horizontalHeaderItem(col).text())
                writer.writerow(headers)
                
                # Записываем данные
                for row in range(self.rowCount()):
                    row_data = []
                    for col in range(self.columnCount()):
                        item = self.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
                    
            return True
        except Exception as e:
            print(f"Ошибка экспорта в файл {filename}: {e}")
            traceback.print_exc()
            return False
    
    def import_from_file(self, filename: str):
        """Импортировать таблицу из файла"""
        try:
            # Определяем разделитель по расширению файла
            if filename.endswith('.csv'):
                delimiter = ','
            else:
                delimiter = '\t'
            
            # Читаем файл
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines:
                return False
            
            # Очищаем таблицу
            self.clear_table()
            
            # Пропускаем заголовок и читаем данные
            header_line = lines[0].strip()
            headers = header_line.split(delimiter)
            
            for line_num, line in enumerate(lines[1:], 2):  # начиная с 2 строки
                line = line.strip()
                if not line:
                    continue
                    
                parts = line.split(delimiter)
                if len(parts) >= 8:  # минимальное количество полей
                    try:
                        params = ParamPSF()
                        
                        # Маппинг колонок
                        col_map = {}
                        for i, header in enumerate(headers):
                            header_lower = header.lower()
                            if 'размер' in header_lower or 'size' in header_lower:
                                col_map['size'] = i
                            elif 'λ' in header or 'длина' in header_lower or 'wavelength' in header_lower:
                                col_map['wavelength'] = i
                            elif 'апертура' in header_lower or 'aperture' in header_lower:
                                col_map['aperture'] = i
                            elif 'ув' in header_lower or 'magnification' in header_lower:
                                col_map['magnification'] = i
                            elif 'расфок' in header_lower or 'defocus' in header_lower:
                                col_map['defocus'] = i
                            elif 'астигм' in header_lower or 'astigmatism' in header_lower:
                                col_map['astigmatism'] = i
                            elif 'охват' in header_lower or 'диаметр' in header_lower or 'diameter' in header_lower or 'pupil' in header_lower:
                                col_map['pupil_diameter'] = i
                            elif 'шаг зр' in header_lower or 'step_pupil' in header_lower:
                                col_map['step_pupil'] = i
                            elif 'шаг предм' in header_lower or 'step_object' in header_lower:
                                col_map['step_object'] = i
                            elif 'шаг изобр' in header_lower or 'step_image' in header_lower:
                                col_map['step_image'] = i
                            elif 'штрель' in header_lower or 'strehl' in header_lower:
                                col_map['strehl'] = i
                            elif 'статус' in header_lower or 'status' in header_lower:
                                col_map['status'] = i
                            elif '№' in header or 'номер' in header_lower or 'num' in header_lower:
                                col_map['num'] = i
                        
                        # Парсим данные
                        if 'size' in col_map:
                            params.size = int(float(parts[col_map['size']])) if parts[col_map['size']] else 512
                        if 'wavelength' in col_map:
                            params.wavelength = float(parts[col_map['wavelength']]) if parts[col_map['wavelength']] else 0.555
                        if 'aperture' in col_map:
                            params.back_aperture = float(parts[col_map['aperture']]) if parts[col_map['aperture']] else 0.5
                        if 'magnification' in col_map:
                            params.magnification = float(parts[col_map['magnification']]) if parts[col_map['magnification']] else 1.0
                        if 'defocus' in col_map:
                            params.defocus = float(parts[col_map['defocus']]) if parts[col_map['defocus']] else 0.0
                        if 'astigmatism' in col_map:
                            params.astigmatism = float(parts[col_map['astigmatism']]) if parts[col_map['astigmatism']] else 0.0
                        if 'pupil_diameter' in col_map:
                            params.pupil_diameter = float(parts[col_map['pupil_diameter']]) if parts[col_map['pupil_diameter']] else 8.0
                        if 'step_pupil' in col_map:
                            params.step_pupil = float(parts[col_map['step_pupil']]) if parts[col_map['step_pupil']] else 0.0625
                        if 'step_object' in col_map:
                            params.step_object = float(parts[col_map['step_object']]) if parts[col_map['step_object']] else 0.13875
                        if 'step_image' in col_map:
                            params.step_image = float(parts[col_map['step_image']]) if parts[col_map['step_image']] else 0.13875
                        
                        # Добавляем строку
                        self.add_row(params)
                        
                        # Если есть число Штреля, устанавливаем его
                        if 'strehl' in col_map and col_map['strehl'] < len(parts) and parts[col_map['strehl']]:
                            row_idx = self.rowCount() - 1
                            strehl_value = parts[col_map['strehl']].strip()
                            if strehl_value:
                                item = QTableWidgetItem(strehl_value)
                                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                                self.setItem(row_idx, 11, item)
                        
                        # Если есть статус, устанавливаем его
                        if 'status' in col_map and col_map['status'] < len(parts) and parts[col_map['status']]:
                            row_idx = self.rowCount() - 1
                            status_value = parts[col_map['status']].strip()
                            if status_value:
                                item = QTableWidgetItem(status_value)
                                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                                self.setItem(row_idx, 12, item)
                            
                    except Exception as e:
                        print(f"Ошибка импорта строки {line_num}: {e}")
                        traceback.print_exc()
                        
            return True
                        
        except Exception as e:
            print(f"Ошибка чтения файла {filename}: {e}")
            traceback.print_exc()
            return False


class PSFMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Расчет ФРТ с таблицей параметров")
        self.resize(1600, 900)

        self.params = ParamPSF()
        self.calculator = PSFCalculator()
        self.current_psf = None
        self.strehl_ratio = 0.0
        self.table_data = []

        self._init_ui()
        self._init_menu_toolbar()
        self._init_dock_widgets()

        self.report_generator = ReportGenerator()
        self.print_log_text = ""  # Для хранения лога для печати
        
    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        
        # ===== ТАБЛИЦА ПАРАМЕТРОВ =====
        table_group = QGroupBox("Таблица параметров и вычислений")
        table_layout = QVBoxLayout(table_group)
        
        self.table_widget = ParameterTable()
        self.table_widget.calculation_complete.connect(self._on_calculation_complete)
        self.table_widget.selection_changed.connect(self._on_table_selection_changed)
        
        # Панель инструментов таблицы (ОБНОВЛЕННАЯ с кнопками печати)
        table_toolbar = QHBoxLayout()
        
        self.btn_add_row = QPushButton("Добавить строку")
        self.btn_add_row.clicked.connect(self._add_table_row)
        
        self.btn_delete_row = QPushButton("Удалить строку")
        self.btn_delete_row.clicked.connect(self._delete_table_row)
        
        self.btn_clear_table = QPushButton("Очистить таблицу")
        self.btn_clear_table.clicked.connect(self._clear_table)
        
        self.btn_settings = QPushButton("Настройки параметров")
        self.btn_settings.clicked.connect(self._show_settings_dialog)
        
        self.btn_recalc_steps = QPushButton("Пересчет шагов")
        self.btn_recalc_steps.clicked.connect(self._recalculate_steps)
        
        # НОВЫЕ КНОПКИ ПЕЧАТИ
        self.btn_preview_report = QPushButton("Предпросмотр отчета")
        self.btn_preview_report.clicked.connect(self._preview_report)
        self.btn_preview_report.setEnabled(False)
        
        self.btn_print_report = QPushButton("Печать отчета")
        self.btn_print_report.clicked.connect(self._print_report)
        self.btn_print_report.setEnabled(False)
        
        self.btn_calc_selected = QPushButton("Вычислить выбранную")
        self.btn_calc_selected.clicked.connect(self._calculate_selected)
        
        self.btn_calc_all = QPushButton("Вычислить все")
        self.btn_calc_all.clicked.connect(self._calculate_all)
        
        table_toolbar.addWidget(self.btn_add_row)
        table_toolbar.addWidget(self.btn_delete_row)
        table_toolbar.addWidget(self.btn_clear_table)
        table_toolbar.addWidget(self.btn_settings)
        table_toolbar.addWidget(self.btn_recalc_steps)
        table_toolbar.addStretch()
        table_toolbar.addWidget(self.btn_preview_report)  # ДОБАВЛЯЕМ
        table_toolbar.addWidget(self.btn_print_report)    # ДОБАВЛЯЕМ
        table_toolbar.addWidget(self.btn_calc_selected)
        table_toolbar.addWidget(self.btn_calc_all)
        
        table_layout.addLayout(table_toolbar)
        table_layout.addWidget(self.table_widget)
        
        main_layout.addWidget(table_group)
        
        # ===== ГРАФИКИ =====
        self.psf_view = PSFView()
        main_layout.addWidget(self.psf_view, 1)
        
        # ===== ЛОГ =====
        self.log_widget = LogWidget()
        main_layout.addWidget(self.log_widget)
        
        # Добавляем несколько строк по умолчанию
        self._add_default_rows()
        
    def _init_dock_widgets(self):
        """Инициализация док-виджетов для деталей вычислений"""
        # Док для информации о выбранной строке
        info_dock = QDockWidget("Информация о выбранной строке", self)
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        
        self.selected_info_label = QLabel("Выберите строку в таблице")
        self.selected_info_label.setWordWrap(True)
        self.selected_info_label.setStyleSheet("padding: 10px; border: 1px solid #ccc;")
        
        info_layout.addWidget(self.selected_info_label)
        info_dock.setWidget(info_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, info_dock)
        
    def _init_menu_toolbar(self):
        menu = self.menuBar()
        
        # Меню Файл (ОБНОВЛЕННОЕ)
        file_menu = menu.addMenu("Файл")
        
        act_new_table = QAction("Новая таблица", self)
        act_load_table = QAction("Загрузить таблицу", self)
        act_save_table = QAction("Сохранить таблицу", self)
        act_export_table = QAction("Экспорт таблицы", self)
        
        # НОВЫЕ ДЕЙСТВИЯ ДЛЯ ПЕЧАТИ
        act_preview_report = QAction("Предпросмотр отчета", self)
        act_print_report = QAction("Печать отчета", self)
        act_export_pdf = QAction("Экспорт в PDF", self)
        
        act_export_image = QAction("Экспорт графиков", self)
        act_exit = QAction("Выход", self)
        
        act_new_table.triggered.connect(self._new_table)
        act_load_table.triggered.connect(self._load_table)
        act_save_table.triggered.connect(self._save_table)
        act_export_table.triggered.connect(self._export_table)
        
        # ПОДКЛЮЧАЕМ НОВЫЕ СИГНАЛЫ
        act_preview_report.triggered.connect(self._preview_report)
        act_print_report.triggered.connect(self._print_report)
        act_export_pdf.triggered.connect(self._export_pdf)
        
        act_export_image.triggered.connect(self._export_all_graphs)
        act_exit.triggered.connect(self.close)
        
        file_menu.addAction(act_new_table)
        file_menu.addSeparator()
        file_menu.addAction(act_load_table)
        file_menu.addAction(act_save_table)
        file_menu.addAction(act_export_table)
        file_menu.addSeparator()
        
        # ДОБАВЛЯЕМ НОВЫЕ ПУНКТЫ МЕНЮ
        file_menu.addAction(act_preview_report)
        file_menu.addAction(act_print_report)
        file_menu.addAction(act_export_pdf)
        file_menu.addSeparator()
        
        file_menu.addAction(act_export_image)
        file_menu.addSeparator()
        file_menu.addAction(act_exit)
        
        # Меню Таблица
        table_menu = menu.addMenu("Таблица")
        
        act_settings = QAction("Настройки параметров", self)
        act_copy_table = QAction("Копировать таблицу", self)
        act_paste_table = QAction("Вставить таблицу", self)
        act_import_csv = QAction("Импорт CSV", self)
        
        act_settings.triggered.connect(self._show_settings_dialog)
        act_copy_table.triggered.connect(self._copy_table)
        act_paste_table.triggered.connect(self._paste_table)
        act_import_csv.triggered.connect(self._import_csv)
        
        table_menu.addAction(act_settings)
        table_menu.addSeparator()
        table_menu.addAction(act_copy_table)
        table_menu.addAction(act_paste_table)
        table_menu.addSeparator()
        table_menu.addAction(act_import_csv)
        
        # Toolbar (ОБНОВЛЕННЫЙ)
        toolbar = QToolBar("Основные действия")
        self.addToolBar(toolbar)
        
        toolbar.addAction(act_new_table)
        toolbar.addAction(act_load_table)
        toolbar.addAction(act_save_table)
        toolbar.addSeparator()
        toolbar.addAction(act_settings)
        toolbar.addAction(act_copy_table)
        toolbar.addSeparator()
        
        # ДОБАВЛЯЕМ НА ПАНЕЛЬ ИНСТРУМЕНТОВ
        toolbar.addAction(act_preview_report)
        toolbar.addAction(act_print_report)
        toolbar.addAction(act_export_image)
        
    def _add_default_rows(self):
        """Добавить несколько строк по умолчанию"""
        default_params = [
            ParamPSF(size=512, wavelength=0.555, defocus=0.0, astigmatism=0.0),
            ParamPSF(size=512, wavelength=0.555, defocus=0.1, astigmatism=0.0),
            ParamPSF(size=512, wavelength=0.555, defocus=0.0, astigmatism=0.05),
            ParamPSF(size=512, wavelength=0.555, defocus=0.1, astigmatism=0.05),
            ParamPSF(size=256, wavelength=0.488, defocus=0.05, astigmatism=0.02),
        ]
        
        # Пересчитываем шаги для каждого набора параметров
        for params in default_params:
            params.recalculate_from_pupil_diameter()
            self.table_widget.add_row(params)
            
    def _add_table_row(self):
        """Добавить новую строку в таблицу"""
        self.table_widget.add_row(self.params)
        self.log_widget.add_log("Добавлена новая строка в таблицу")
        
    def _delete_table_row(self):
        """Удалить выбранную строку из таблицы"""
        self.table_widget.delete_selected_row()
        self.log_widget.add_log("Удалена выбранная строка из таблицы")
        
    def _clear_table(self):
        """Очистить таблицу"""
        reply = QMessageBox.question(
            self,
            "Очистка таблицы",
            "Вы уверены, что хотите очистить всю таблицу?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.table_widget.clear_table()
            self.log_widget.add_log("Таблица очищена")
            
    def _recalculate_steps(self):
        """Пересчитать шаги для всех строк"""
        self.table_widget.recalculate_steps()
        self.log_widget.add_log("Выполнен пересчет шагов для всей таблицы")
        QMessageBox.information(self, "Пересчет шагов", "Параметры дискретизации пересчитаны")
        
    def _show_settings_dialog(self):
        """Показать диалог настроек параметров"""
        # Получаем параметры из выбранной строки или создаем новые
        params = self.table_widget.get_selected_params()
        if params is None:
            params = ParamPSF()
            
        # Создаем и показываем диалог
        dialog = SettingsDialog(params, self)
        dialog.settings_changed.connect(self._on_settings_changed)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.log_widget.add_log("Параметры дискретизации обновлены")
            
    def _on_settings_changed(self, params: ParamPSF):
        """Обработчик изменения настроек параметров"""
        # Обновляем текущие параметры
        self.params = params
        
        # Обновляем выбранную строку в таблице
        selected_rows = self.table_widget.get_selected_rows()
        if selected_rows:
            row = selected_rows[0]
            self._update_table_row_with_params(row, params)
            
        # Обновляем отображение
        if selected_rows:
            self._on_table_selection_changed(selected_rows[0])
        
    def _update_table_row_with_params(self, row: int, params: ParamPSF):
        """Обновить строку таблицы с новыми параметрами"""
        if row < self.table_widget.rowCount():
            # Обновляем значения в таблице
            self.table_widget.item(row, 1).setText(str(params.size))
            self.table_widget.item(row, 2).setText(f"{params.wavelength:.3f}")
            self.table_widget.item(row, 3).setText(f"{params.back_aperture:.3f}")
            self.table_widget.item(row, 4).setText(f"{params.magnification:.1f}")
            self.table_widget.item(row, 5).setText(f"{params.defocus:.3f}")
            self.table_widget.item(row, 6).setText(f"{params.astigmatism:.3f}")
            self.table_widget.item(row, 7).setText(f"{params.pupil_diameter:.3f}")
            self.table_widget.item(row, 8).setText(f"{params.step_pupil:.6f}")
            self.table_widget.item(row, 9).setText(f"{params.step_object:.6f}")
            self.table_widget.item(row, 10).setText(f"{params.step_image:.6f}")
            
            # Обновляем список параметров
            if row < len(self.table_widget.current_params_list):
                self.table_widget.current_params_list[row] = params
            else:
                self.table_widget.current_params_list.append(params)
            
    def _calculate_selected(self):
        """Вычислить выбранную строку"""
        self.table_widget.calculate_selected()
        
    def _calculate_all(self):
        """Вычислить все строки"""
        reply = QMessageBox.question(
            self,
            "Вычисление всей таблицы",
            "Выполнить расчет ФРТ для всех строк таблицы?\nЭто может занять некоторое время.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.table_widget.calculate_all()
            self.log_widget.add_log("Выполнен расчет всей таблицы")
            
    def _on_calculation_complete(self, row: int, strehl_ratio: float):
        """Обработчик завершения расчета строки"""
        self.log_widget.add_log(f"Строка {row+1}: расчет завершен, Штрель = {strehl_ratio:.6f}")
        
    def _on_table_selection_changed(self, row: int):
        """Обработчик изменения выбранной строки в таблице"""
        params = self.table_widget.get_selected_params()
        strehl = self.table_widget.get_selected_strehl()
        
        if params:
            # Обновляем информацию
            step_microns = params.calculate_step_microns()
            info_text = f"""
            <b>Строка {row+1}:</b><br><br>
            <b>Основные параметры:</b><br>
            • Размер: {params.size}<br>
            • λ: {params.wavelength:.3f} мкм<br>
            • Апертура: {params.back_aperture:.3f}<br>
            • Увеличение: {params.magnification:.1f}<br>
            • Расфокусировка: {params.defocus:.3f}<br>
            • Астигматизм: {params.astigmatism:.3f}<br><br>
            <b>Параметры дискретизации:</b><br>
            • Охват зрачка: {params.pupil_diameter:.3f} к.ед.<br>
            • Шаг по зрачку: {params.step_pupil:.6f} к.ед.<br>
            • Шаг по предмету: {params.step_object:.6f} к.ед.<br>
            • Шаг по изображению: {params.step_image:.6f} к.ед.<br>
            • Шаг в изображении: {step_microns:.6f} мкм<br><br>
            <b>Число Штреля:</b> {strehl:.6f}
            """
            self.selected_info_label.setText(info_text)
            
            # Вычисляем и отображаем PSF
            try:
                self.current_psf, self.strehl_ratio = self.calculator.compute(params)
                step_microns = self.calculator._step_im_microns
                self.psf_view.show_psf(self.current_psf, step_microns)
                self.log_widget.add_log(f"Отображена ФРТ для строки {row+1}")
            except Exception as e:
                self.log_widget.add_log(f"Ошибка отображения ФРТ: {str(e)}")
                traceback.print_exc()
                
    def _new_table(self):
        """Создать новую таблицу"""
        reply = QMessageBox.question(
            self,
            "Новая таблица",
            "Создать новую таблицу? Текущие данные будут потеряны.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.table_widget.clear_table()
            self._add_default_rows()
            self.log_widget.add_log("Создана новая таблица")
            
    def _load_table(self):
        """Загрузить таблицу из файла"""
        path, filter = QFileDialog.getOpenFileName(
            self,
            "Загрузить таблицу",
            "",
            "Все файлы (*.*);;CSV (*.csv);;Текстовые (*.txt);;Tab разделитель (*.tsv);;Excel (*.xlsx)"
        )
        
        if path:
            try:
                success = self.table_widget.import_from_file(path)
                if success:
                    self.log_widget.add_log(f"Таблица загружена из: {path}")
                    QMessageBox.information(self, "Успех", "Таблица успешно загружена")
                else:
                    QMessageBox.warning(self, "Предупреждение", "Не удалось загрузить таблицу")
                    self.log_widget.add_log(f"Ошибка: не удалось загрузить таблицу из {path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка загрузки", str(e))
                self.log_widget.add_log(f"Ошибка загрузки таблицы: {str(e)}")
                traceback.print_exc()
                
    def _save_table(self):
        """Сохранить таблицу в файл"""
        if self.table_widget.rowCount() == 0:
            QMessageBox.warning(self, "Предупреждение", "Таблица пуста")
            return
            
        path, filter = QFileDialog.getSaveFileName(
            self,
            "Сохранить таблицу",
            f"psf_table_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "CSV (*.csv);;Текстовые с табуляцией (*.txt);;Все файлы (*.*)"
        )
        
        if path:
            try:
                # Если расширение не указано, добавляем .txt
                if not any(path.endswith(ext) for ext in ['.csv', '.txt', '.tsv']):
                    path += '.txt'
                
                success = self.table_widget.export_to_file(path)
                if success:
                    self.log_widget.add_log(f"Таблица сохранена в: {path}")
                    QMessageBox.information(self, "Успех", "Таблица успешно сохранена")
                else:
                    QMessageBox.warning(self, "Предупреждение", "Не удалось сохранить таблицу")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка сохранения", str(e))
                self.log_widget.add_log(f"Ошибка сохранения таблицы: {str(e)}")
                traceback.print_exc()
                
    def _export_table(self):
        """Экспорт таблицы (алиас для save_table)"""
        self._save_table()
        
    def _copy_table(self):
        """Копировать таблицу в буфер обмена"""
        self.table_widget.copy_to_clipboard()
        
    def _paste_table(self):
        """Вставить таблицу из буфера обмена"""
        try:
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            if not text:
                QMessageBox.warning(self, "Предупреждение", "Буфер обмена пуст")
                return
            
            # Создаем временный файл
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(text)
                temp_file = f.name
            
            # Импортируем из временного файла
            success = self.table_widget.import_from_file(temp_file)
            
            # Удаляем временный файл
            try:
                os.unlink(temp_file)
            except:
                pass
            
            if success:
                self.log_widget.add_log("Данные вставлены из буфера обмена")
                QMessageBox.information(self, "Успех", "Данные успешно вставлены")
            else:
                QMessageBox.warning(self, "Предупреждение", "Не удалось вставить данные")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка вставки", str(e))
            self.log_widget.add_log(f"Ошибка вставки: {str(e)}")
            traceback.print_exc()
        
    def _import_csv(self):
        """Импортировать данные из CSV"""
        self._load_table()  # Используем тот же диалог
                
    def _export_all_graphs(self):
        """Экспортировать все графики в PNG"""
        if self.current_psf is None:
            QMessageBox.warning(self, "Предупреждение", "Нет данных для экспорта")
            return
            
        # Создаем диалог для выбора директории
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для сохранения графиков",
            ""
        )
        
        if not dir_path:
            return
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 1. Сохраняем основное изображение PSF
            fig1, ax1 = plt.subplots(figsize=(10, 8))
            im1 = ax1.imshow(self.current_psf, cmap='inferno')
            ax1.set_title(f'ФРТ (Strehl ratio: {self.strehl_ratio:.4f})')
            plt.colorbar(im1, ax=ax1, label='Интенсивность')
            psf_path = f"{dir_path}/psf_{timestamp}.png"
            fig1.savefig(psf_path, dpi=300, bbox_inches='tight')
            plt.close(fig1)
            
            # 2. Сохраняем сечения
            fig2, (ax2, ax3) = plt.subplots(1, 2, figsize=(12, 5))
            
            size = self.current_psf.shape[0]
            center = size // 2
            x_slice = self.current_psf[center, :]
            y_slice = self.current_psf[:, center]
            
            # Сечение по X
            ax2.plot(x_slice, 'b-', linewidth=2)
            ax2.set_title('Сечение по X')
            ax2.set_xlabel('Координата')
            ax2.set_ylabel('Интенсивность')
            ax2.grid(True, alpha=0.3)
            
            # Сечение по Y
            ax3.plot(y_slice, 'r-', linewidth=2)
            ax3.set_title('Сечение по Y')
            ax3.set_xlabel('Координата')
            ax3.set_ylabel('Интенсивность')
            ax3.grid(True, alpha=0.3)
            
            slices_path = f"{dir_path}/slices_{timestamp}.png"
            fig2.savefig(slices_path, dpi=300, bbox_inches='tight')
            plt.close(fig2)
            
            # 3. Пытаемся сохранить 3D график
            graph_files = [psf_path, slices_path]
            try:
                from mpl_toolkits.mplot3d import Axes3D
                fig3 = plt.figure(figsize=(10, 8))
                ax3d = fig3.add_subplot(111, projection='3d')
                
                X, Y = np.meshgrid(np.arange(size), np.arange(size))
                surf = ax3d.plot_surface(X, Y, self.current_psf, cmap='inferno',
                                       linewidth=0, antialiased=False, alpha=0.8)
                ax3d.set_title('3D вид ФРТ')
                ax3d.set_xlabel('X')
                ax3d.set_ylabel('Y')
                ax3d.set_zlabel('Интенсивность')
                
                ax3d.view_init(elev=30, azim=45)
                
                fig3.colorbar(surf, ax=ax3d, shrink=0.5, aspect=5)
                threed_path = f"{dir_path}/3d_psf_{timestamp}.png"
                fig3.savefig(threed_path, dpi=300, bbox_inches='tight')
                plt.close(fig3)
                
                graph_files.append(threed_path)
            except Exception as e3d:
                print(f"Не удалось создать 3D график: {e3d}")
            
            self.log_widget.add_log(f"Графики экспортированы в папку: {dir_path}")
            
            message = "Графики успешно сохранены:\n\n"
            for file in graph_files:
                message += f"• {file}\n"
            
            QMessageBox.information(self, "Экспорт графиков", message)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка экспорта графиков", str(e))
            self.log_widget.add_log(f"Ошибка экспорта графиков: {str(e)}")
            traceback.print_exc()
    def _collect_log_for_report(self):
        """Собрать лог для отчета"""
        try:
            # Получаем текст из лог-виджета
            log_text = self.log_widget.text_edit.toPlainText()
            
            # Добавляем информацию о текущем выборе
            selected_rows = self.table_widget.get_selected_rows()
            if selected_rows:
                row = selected_rows[0]
                log_text += f"\n\n--- Информация для отчета ---"
                log_text += f"\nВыбрана строка: {row + 1}"
                
                params = self.table_widget.get_selected_params()
                if params:
                    log_text += f"\nРазмер: {params.size}"
                    log_text += f"\nДлина волны: {params.wavelength:.3f} мкм"
                    log_text += f"\nЧисло Штреля: {self.strehl_ratio:.6f}"
            
            return log_text
        except Exception as e:
            print(f"Ошибка сбора лога: {e}")
            return ""

    def _preview_report(self):
        """Показать предпросмотр отчета"""
        if self.current_psf is None:
            QMessageBox.warning(self, "Предупреждение", "Нет данных для создания отчета. Сначала выполните расчет.")
            return
        
        # Получаем текущие параметры
        params = self.table_widget.get_selected_params()
        if params is None:
            QMessageBox.warning(self, "Предупреждение", "Не выбрана строка с параметрами.")
            return
        
        # # Собираем лог
        # log_text = self._collect_log_for_report()
        
        # Вычисляем шаг в микронах
        step_microns = params.calculate_step_microns()
        
        # Показываем диалог предпросмотра
        dialog = PreviewDialog(
            params, self.current_psf, self.strehl_ratio, 
            step_microns,  self
        )
        dialog.exec()

    def _print_report(self):
        """Напечатать отчет"""
        if self.current_psf is None:
            QMessageBox.warning(self, "Предупреждение", "Нет данных для печати отчета. Сначала выполните расчет.")
            return
        
        # Получаем текущие параметры
        params = self.table_widget.get_selected_params()
        if params is None:
            QMessageBox.warning(self, "Предупреждение", "Не выбрана строка с параметрами.")
            return
        
        # Вычисляем шаг в микронах
        step_microns = params.calculate_step_microns()
        
        # Создаем диалог выбора файла для PDF
        from PyQt6.QtWidgets import QFileDialog
        from PyQt6.QtCore import QDateTime
        from PyQt6.QtWidgets import QProgressBar

        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить отчет в PDF",
            f"psf_report_{QDateTime.currentDateTime().toString('yyyyMMdd_hhmmss')}.pdf",
            "PDF files (*.pdf);;All files (*.*)"
        )
        
        if not filename:
            return
        
        # Создаем диалог прогресса с возможностью отмены
        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle("Генерация отчета")
        progress_dialog.setModal(True)
        progress_dialog.setFixedSize(300, 100)
        
        progress_layout = QVBoxLayout(progress_dialog)
        
        progress_label = QLabel("Идет создание PDF отчета...")
        progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(progress_label)
        
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 0)  # Неопределенный прогресс
        progress_layout.addWidget(progress_bar)
        
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(progress_dialog.reject)
        progress_layout.addWidget(cancel_button, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Запускаем генерацию в отдельном потоке
        from PyQt6.QtCore import QThread, pyqtSignal
        import traceback
        
        class ReportWorker(QThread):
            finished = pyqtSignal(bool, str)
            error = pyqtSignal(str)
            
            def __init__(self, generator, params, psf_data, strehl_ratio, step_microns, filename):
                super().__init__()
                self.generator = generator
                self.params = params
                self.psf_data = psf_data
                self.strehl_ratio = strehl_ratio
                self.step_microns = step_microns
                self.filename = filename
                
            def run(self):
                try:
                    success = self.generator.generate_report(
                        self.params, self.psf_data, self.strehl_ratio,
                        self.step_microns, self.filename
                    )
                    self.finished.emit(success, self.filename)
                except Exception as e:
                    self.error.emit(str(e))
        
        # Создаем и запускаем worker
        self.report_worker = ReportWorker(
            self.report_generator, params, self.current_psf, 
            self.strehl_ratio, step_microns, filename
        )
        
        # Подключаем сигналы
        def on_finished(success, filename):
            progress_dialog.close()
            if success:
                QMessageBox.information(
                    self, 
                    "Отчет создан", 
                    f"Отчет успешно сохранен в файл:\n{filename}"
                )
                self.log_widget.add_log(f"Отчет сохранен в PDF: {filename}")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось создать отчет")
        
        def on_error(error_msg):
            progress_dialog.close()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании отчета:\n{error_msg}")
            self.log_widget.add_log(f"Ошибка создания отчета: {error_msg}")
            print(f"Ошибка создания отчета: {error_msg}")
            traceback.print_exc()
        
        def on_cancel():
            if self.report_worker.isRunning():
                self.report_worker.terminate()
                self.report_worker.wait()
            progress_dialog.close()
        
        self.report_worker.finished.connect(on_finished)
        self.report_worker.error.connect(on_error)
        progress_dialog.rejected.connect(on_cancel)
        
        # Показываем диалог и запускаем worker
        progress_dialog.show()
        self.report_worker.start()

    def _export_pdf(self):
        """Алиас для печати отчета"""
        self._print_report()

    def _on_calculation_complete(self, row: int, strehl_ratio: float):
        """Обработчик завершения расчета строки (ОБНОВЛЕННЫЙ)"""
        self.log_widget.add_log(f"Строка {row+1}: расчет завершен, Штрель = {strehl_ratio:.6f}")
        
        # Включаем кнопки печати после расчета
        self.btn_preview_report.setEnabled(True)
        self.btn_print_report.setEnabled(True)

    def _on_table_selection_changed(self, row: int):
        """Обработчик изменения выбранной строки в таблице (ОБНОВЛЕННЫЙ)"""
        params = self.table_widget.get_selected_params()
        strehl = self.table_widget.get_selected_strehl()
        
        if params:
            # Обновляем информацию
            step_microns = params.calculate_step_microns()
            info_text = f"""
            <b>Строка {row+1}:</b><br><br>
            <b>Основные параметры:</b><br>
            • Размер: {params.size}<br>
            • λ: {params.wavelength:.3f} мкм<br>
            • Апертура: {params.back_aperture:.3f}<br>
            • Увеличение: {params.magnification:.1f}<br>
            • Расфокусировка: {params.defocus:.3f}<br>
            • Астигматизм: {params.astigmatism:.3f}<br><br>
            <b>Параметры дискретизации:</b><br>
            • Охват зрачка: {params.pupil_diameter:.3f} к.ед.<br>
            • Шаг по зрачку: {params.step_pupil:.6f} к.ед.<br>
            • Шаг по предмету: {params.step_object:.6f} к.ед.<br>
            • Шаг по изображению: {params.step_image:.6f} к.ед.<br>
            • Шаг в изображении: {step_microns:.6f} мкм<br><br>
            <b>Число Штреля:</b> {strehl:.6f}
            """
            self.selected_info_label.setText(info_text)
            
            # Вычисляем и отображаем PSF
            try:
                self.current_psf, self.strehl_ratio = self.calculator.compute(params)
                step_microns = self.calculator._step_im_microns
                self.psf_view.show_psf(self.current_psf, step_microns)
                self.log_widget.add_log(f"Отображена ФРТ для строки {row+1}")
                
                # Включаем кнопки печати
                self.btn_preview_report.setEnabled(True)
                self.btn_print_report.setEnabled(True)
                
            except Exception as e:
                self.log_widget.add_log(f"Ошибка отображения ФРТ: {str(e)}")
                traceback.print_exc()