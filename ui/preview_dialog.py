from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextBrowser, 
    QPushButton, QLabel, QGroupBox, QProgressBar
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QTextDocument
from ui.report_generator import ReportGenerator
import tempfile
import os


class PreviewDialog(QDialog):
    """Диалог предпросмотра отчета"""
    
    def __init__(self, params, psf_data, strehl_ratio, step_microns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Предпросмотр отчета")
        self.resize(900, 700)
        
        self.params = params
        self.psf_data = psf_data
        self.strehl_ratio = strehl_ratio
        self.step_microns = step_microns
        
        self.report_generator = ReportGenerator()
        
        self._init_ui()
        self._generate_preview()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Заголовок
        title_label = QLabel("Предпросмотр отчета о расчете ФРТ")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2E5A88; padding: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Браузер для отображения HTML
        self.preview_browser = QTextBrowser()
        self.preview_browser.setOpenExternalLinks(True)
        layout.addWidget(self.preview_browser, 1)
        
        # Индикатор прогресса
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        self.print_button = QPushButton("Печать отчета")
        self.print_button.clicked.connect(self._print_report)
        self.print_button.setEnabled(False)
        
        self.export_button = QPushButton("Экспорт в PDF")
        self.export_button.clicked.connect(self._export_pdf)
        
        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.clicked.connect(self._generate_preview)
        
        self.close_button = QPushButton("Закрыть")
        self.close_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.print_button)
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
    def _generate_preview(self):
        """Сгенерировать предпросмотр"""
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Индикатор неопределенного прогресса
            
            # Генерируем HTML предпросмотр (без лога)
            html_content = self.report_generator.generate_preview(
                self.params, self.psf_data, self.strehl_ratio, 
                self.step_microns  # Убрали log_text
            )
            
            # Отображаем в браузере
            self.preview_browser.setHtml(html_content)
            
            self.print_button.setEnabled(True)
            
        except Exception as e:
            self.preview_browser.setHtml(f"<h1>Ошибка генерации предпросмотра</h1><p>{str(e)}</p>")
            print(f"Ошибка генерации предпросмотра: {e}")
            
        finally:
            self.progress_bar.setVisible(False)
            
    def _print_report(self):
        """Печать отчета"""
        try:
            # Создаем временный PDF файл
            temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_file.close()
            
            # Генерируем PDF (без лога)
            success = self.report_generator.generate_report(
                self.params, self.psf_data, self.strehl_ratio,
                self.step_microns, temp_file.name  # Убрали log_text
            )
            
            if success:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(
                    self, 
                    "Печать отчета", 
                    f"Отчет сохранен в файл: {temp_file.name}\n\n"
                    "В реальном приложении здесь будет открыт диалог печати."
                )
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось сгенерировать отчет для печати")
                
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Ошибка печати", f"Ошибка при подготовке к печати: {str(e)}")
            print(f"Ошибка печати: {e}")
            
        finally:
            # Удаляем временный файл
            try:
                os.unlink(temp_file.name)
            except:
                pass
                
    def _export_pdf(self):
        """Экспорт отчета в PDF"""
        from PyQt6.QtWidgets import QFileDialog
        from PyQt6.QtCore import QDateTime
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт отчета в PDF",
            f"report_psf_{QDateTime.currentDateTime().toString('yyyyMMdd_hhmmss')}.pdf",
            "PDF files (*.pdf);;All files (*.*)"
        )
        
        if filename:
            try:
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 0)
                
                # Генерируем PDF (без лога)
                success = self.report_generator.generate_report(
                    self.params, self.psf_data, self.strehl_ratio,
                    self.step_microns, filename  # Убрали log_text
                )
                
                if success:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.information(
                        self, 
                        "Экспорт завершен", 
                        f"Отчет успешно экспортирован в файл:\n{filename}"
                    )
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось экспортировать отчет")
                    
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Ошибка экспорта", f"Ошибка при экспорте отчета: {str(e)}")
                print(f"Ошибка экспорта: {e}")
                
            finally:
                self.progress_bar.setVisible(False)