import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib
matplotlib.use('Agg')  # Для работы без GUI
import os


class ReportGenerator:
    """Генератор отчетов для печати результатов вычислений"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._register_fonts()
        self._create_custom_styles()
        
    def _register_fonts(self):
        """Регистрация шрифтов с поддержкой кириллицы"""
        try:
            # Пробуем найти стандартные шрифты с кириллицей
            font_paths = [
                # Linux
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                # Windows
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/times.ttf',
                # macOS
                '/Library/Fonts/Arial.ttf',
                '/System/Library/Fonts/Helvetica.ttf',
                # Текущая директория
                'fonts/arial.ttf',
                'arial.ttf'
            ]
            
            registered = False
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        # Регистрируем обычный шрифт
                        pdfmetrics.registerFont(TTFont('Arial', font_path))
                        # Регистрируем жирный шрифт (пробуем найти или использовать тот же)
                        pdfmetrics.registerFont(TTFont('Arial-Bold', font_path))
                        pdfmetrics.registerFontFamily('Arial', normal='Arial', bold='Arial-Bold')
                        registered = True
                        print(f"Зарегистрирован шрифт: {font_path}")
                        break
                    except Exception as e:
                        print(f"Не удалось зарегистрировать шрифт {font_path}: {e}")
            
            if not registered:
                print("Предупреждение: не найдены шрифты с кириллицей, используем стандартные")
                # Используем стандартные шрифты
                pdfmetrics.registerFont(TTFont('Arial', 'Helvetica'))
                pdfmetrics.registerFont(TTFont('Arial-Bold', 'Helvetica-Bold'))
                
        except Exception as e:
            print(f"Ошибка регистрации шрифтов: {e}")
            # Используем стандартные шрифты как запасной вариант
            pdfmetrics.registerFont(TTFont('Arial', 'Helvetica'))
            pdfmetrics.registerFont(TTFont('Arial-Bold', 'Helvetica-Bold'))
    
    def _create_custom_styles(self):
        """Создание пользовательских стилей"""
        # Заголовок отчета
        if 'ReportTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='ReportTitle',
                parent=self.styles['Title'],
                fontName='Arial-Bold',
                fontSize=16,
                spaceAfter=20,
                alignment=TA_CENTER
            ))
        
        # Заголовок раздела
        if 'SectionTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SectionTitle',
                parent=self.styles['Heading1'],
                fontName='Arial-Bold',
                fontSize=14,
                spaceAfter=10,
                spaceBefore=15,
                textColor=colors.HexColor('#2E5A88')
            ))
        
        # Подзаголовок
        if 'SubTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SubTitle',
                parent=self.styles['Heading2'],
                fontName='Arial',
                fontSize=12,
                spaceAfter=6,
                spaceBefore=12,
                textColor=colors.HexColor('#444444')
            ))
        
        # Основной текст
        if 'ReportBodyText' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='ReportBodyText',
                parent=self.styles['Normal'],
                fontName='Arial',
                fontSize=10,
                spaceAfter=5,
                leading=12
            ))
        
        # Мелкий текст
        if 'SmallText' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SmallText',
                parent=self.styles['Normal'],
                fontName='Arial',
                fontSize=8,
                spaceAfter=3,
                leading=10
            ))
    
    def generate_report(self, params, psf_data, strehl_ratio, step_microns, filename):
        """Сгенерировать PDF отчет"""
        try:
            # Создаем документ с указанием кодировки
            doc = SimpleDocTemplate(
                filename,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=3*cm,  # Больший верхний отступ для колонтитула
                bottomMargin=2*cm,
                encoding='utf-8'
            )
            
            story = []
            
            # Университет ИТМО вверху документа (будет добавлено в колонтитуле)
            # Основной контент начинается здесь
            
            # Заголовок отчета
            story.append(Paragraph("ОТЧЕТ О РАСЧЕТЕ ФРТ", self.styles['ReportTitle']))
            story.append(Paragraph(f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}", 
                                  self.styles['SmallText']))
            story.append(Spacer(1, 15))
            
            # Раздел 1: Параметры расчета
            story.append(Paragraph("1. ПАРАМЕТРЫ РАСЧЕТА", self.styles['SectionTitle']))
            
            # Основные параметры
            story.append(Paragraph("Основные параметры:", self.styles['SubTitle']))
            
            # Подготовка данных для таблицы
            params_table_data = [
                ["Параметр", "Значение", "Единицы измерения"],
                ["Размер (точек)", str(params.size), "шт"],
                ["Длина волны", f"{params.wavelength:.3f}", "мкм"],
                ["Задняя апертура", f"{params.back_aperture:.3f}", ""],
                ["Увеличение", f"{params.magnification:.1f}", ""],
                ["Расфокусировка", f"{params.defocus:.3f}", "волн"],
                ["Астигматизм", f"{params.astigmatism:.3f}", "волн"],
                ["Охват зрачка", f"{params.pupil_diameter:.3f}", "к.ед."],
                ["Шаг по зрачку", f"{params.step_pupil:.6f}", "к.ед."],
                ["Шаг по предмету", f"{params.step_object:.6f}", "к.ед."],
                ["Шаг по изображению", f"{params.step_image:.6f}", "к.ед."],
                ["Шаг в изображении", f"{step_microns:.6f}", "мкм"]
            ]
            
            # Преобразуем строки в Paragraph с указанием шрифта
            table_data = []
            for row in params_table_data:
                table_row = []
                for cell in row:
                    if row == params_table_data[0]:  # Заголовки
                        table_row.append(Paragraph(cell, ParagraphStyle(
                            name='TableHeader',
                            fontName='Arial-Bold',
                            fontSize=10,
                            alignment=TA_CENTER
                        )))
                    else:
                        table_row.append(Paragraph(cell, ParagraphStyle(
                            name='TableCell',
                            fontName='Arial',
                            fontSize=9,
                            alignment=TA_LEFT
                        )))
                table_data.append(table_row)
            
            params_table = Table(table_data, colWidths=[5*cm, 3*cm, 3*cm])
            params_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8E8E8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#000000')),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Arial-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F8F8')),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#000000')),
                ('ALIGN', (0, 1), (1, -1), 'LEFT'),
                ('ALIGN', (2, 1), (2, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Arial'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#C0C0C0')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            
            story.append(params_table)
            story.append(Spacer(1, 20))
            
            # Раздел 2: Результаты
            story.append(Paragraph("2. РЕЗУЛЬТАТЫ РАСЧЕТА", self.styles['SectionTitle']))
            
            # Число Штреля
            story.append(Paragraph(f"Число Штреля: <font name='Arial-Bold' color='#2E5A88'>{strehl_ratio:.6f}</font>", 
                                  self.styles['ReportBodyText']))
            
            # Оценка качества
            quality = "Отличное" if strehl_ratio > 0.8 else "Хорошее" if strehl_ratio > 0.6 else "Удовлетворительное" if strehl_ratio > 0.4 else "Плохое"
            quality_color = "#2E5A88" if strehl_ratio > 0.8 else "#4A7729" if strehl_ratio > 0.6 else "#D4A017" if strehl_ratio > 0.4 else "#C42B1C"
            
            story.append(Paragraph(f"Качество системы: <font name='Arial-Bold' color='{quality_color}'>{quality}</font>", 
                                  self.styles['ReportBodyText']))
            story.append(Spacer(1, 20))
            
            # Раздел 3: Графики
            story.append(Paragraph("3. ГРАФИЧЕСКИЕ РЕЗУЛЬТАТЫ", self.styles['SectionTitle']))
            
            # Создаем и добавляем графики
            try:
                # Изображение PSF
                story.append(Paragraph("Распределение интенсивности ФРТ:", self.styles['SubTitle']))
                psf_image = self._create_psf_image(psf_data, strehl_ratio)
                story.append(psf_image)
                story.append(Spacer(1, 15))
                
                # Сечения PSF
                story.append(Paragraph("Сечения ФРТ по осям:", self.styles['SubTitle']))
                slices_image = self._create_slices_image(psf_data)
                story.append(slices_image)
                story.append(Spacer(1, 15))
                
            except Exception as e:
                story.append(Paragraph(f"Ошибка создания графиков: {str(e)}", self.styles['ReportBodyText']))
            
            # Убираем раздел "Лог вычислений" и "Заключение" по требованию
            
            # Добавляем небольшой отступ в конце
            story.append(Spacer(1, 10))
            
            # Строим PDF с колонтитулами
            doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
            
            return True
            
        except Exception as e:
            print(f"Ошибка генерации отчета: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _add_header_footer(self, canvas, doc):
        """Добавить колонтитулы на каждую страницу"""
        canvas.saveState()
        
        # ВЕРХНИЙ КОЛОНТИТУЛ (Университет ИТМО)
        try:
            canvas.setFont('Arial-Bold', 10)
        except:
            canvas.setFont('Helvetica-Bold', 10)
        
        # Университет ИТМО - слева
        canvas.drawString(2*cm, doc.pagesize[1] - 1.5*cm, "Университет ИТМО")
        
        # Лабораторная работа - по центру
        canvas.drawCentredString(doc.pagesize[0]/2, doc.pagesize[1] - 1.5*cm, "Лабораторная работа №3")
        
        # Дата - справа
        canvas.drawRightString(doc.pagesize[0] - 2*cm, doc.pagesize[1] - 1.5*cm, 
                             datetime.now().strftime('%d.%m.%Y'))
        
        # Линия под колонтитулом
        canvas.line(2*cm, doc.pagesize[1] - 1.8*cm, 
                   doc.pagesize[0] - 2*cm, doc.pagesize[1] - 1.8*cm)
        
        # НИЖНИЙ КОЛОНТИТУЛ (номер страницы)
        try:
            canvas.setFont('Arial', 9)
        except:
            canvas.setFont('Helvetica', 9)
        
        page_num = canvas.getPageNumber()
        canvas.drawCentredString(doc.pagesize[0]/2, 1*cm, f"Страница {page_num}")
        
        canvas.restoreState()
    
    def _create_psf_image(self, psf_data, strehl_ratio):
        """Создать изображение PSF для отчета"""
        try:
            # Настройка matplotlib для поддержки кириллицы
            plt.rcParams['font.family'] = 'DejaVu Sans'
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            
            # Создаем фигуру
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Отображаем PSF
            im = ax.imshow(psf_data, cmap='inferno', aspect='auto')
            ax.set_title(f'Функция рассеяния точки', fontsize=12)
            ax.set_xlabel('Координата X, пиксели', fontsize=10)
            ax.set_ylabel('Координата Y, пиксели', fontsize=10)
            
            # Добавляем цветовую шкалу
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('Интенсивность', fontsize=10)
            
            # Добавляем текст с числом Штреля
            fig.text(0.02, 0.98, f'Число Штреля: {strehl_ratio:.4f}', 
                    fontsize=10, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            # Сохраняем в буфер
            buf = io.BytesIO()
            plt.tight_layout()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            buf.seek(0)
            return Image(buf, width=14*cm, height=10*cm)
            
        except Exception as e:
            print(f"Ошибка создания изображения PSF: {e}")
            # Возвращаем текстовое сообщение вместо изображения
            return Paragraph(f"Не удалось создать изображение ФРТ: {str(e)}", 
                           ParagraphStyle(name='ErrorText', fontName='Arial', fontSize=10))
    
    def _create_slices_image(self, psf_data):
        """Создать изображение сечений PSF для отчета"""
        try:
            # Настройка matplotlib для поддержки кириллицы
            plt.rcParams['font.family'] = 'DejaVu Sans'
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            
            # Создаем фигуру с двумя подграфиками
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
            
            size = psf_data.shape[0]
            center = size // 2
            
            # Сечение по X
            x_slice = psf_data[center, :]
            ax1.plot(x_slice, 'b-', linewidth=2)
            ax1.set_title('Сечение по оси X', fontsize=11)
            ax1.set_xlabel('Координата X, пиксели', fontsize=9)
            ax1.set_ylabel('Интенсивность', fontsize=9)
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(labelsize=8)
            
            # Сечение по Y
            y_slice = psf_data[:, center]
            ax2.plot(y_slice, 'r-', linewidth=2)
            ax2.set_title('Сечение по оси Y', fontsize=11)
            ax2.set_xlabel('Координата Y, пиксели', fontsize=9)
            ax2.set_ylabel('Интенсивность', fontsize=9)
            ax2.grid(True, alpha=0.3)
            ax2.tick_params(labelsize=8)
            
            plt.tight_layout()
            
            # Сохраняем в буфер
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            buf.seek(0)
            return Image(buf, width=14*cm, height=6*cm)
            
        except Exception as e:
            print(f"Ошибка создания изображения сечений: {e}")
            # Возвращаем текстовое сообщение вместо изображения
            return Paragraph(f"Не удалось создать сечения ФРТ: {str(e)}", 
                           ParagraphStyle(name='ErrorText', fontName='Arial', fontSize=10))
    
    def generate_preview(self, params, psf_data, strehl_ratio, step_microns):
        """Сгенерировать HTML предпросмотр отчета"""
        try:
            # Определяем качество
            quality = "Отличное" if strehl_ratio > 0.8 else "Хорошее" if strehl_ratio > 0.6 else "Удовлетворительное" if strehl_ratio > 0.4 else "Плохое"
            quality_color = "#2E5A88" if strehl_ratio > 0.8 else "#4A7729" if strehl_ratio > 0.6 else "#D4A017" if strehl_ratio > 0.4 else "#C42B1C"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Предпросмотр отчета ФРТ</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
                    .report {{ background-color: white; padding: 40px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
                    .header {{ text-align: center; border-bottom: 2px solid #2E5A88; padding-bottom: 20px; margin-bottom: 30px; }}
                    .title {{ color: #2E5A88; font-size: 24px; margin-bottom: 10px; }}
                    .date {{ color: #666; font-size: 14px; }}
                    .section {{ margin-bottom: 30px; }}
                    .section-title {{ color: #2E5A88; font-size: 18px; border-left: 4px solid #2E5A88; padding-left: 10px; margin-bottom: 15px; }}
                    .subsection-title {{ color: #444; font-size: 16px; margin-bottom: 10px; }}
                    .param-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                    .param-table th, .param-table td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
                    .param-table th {{ background-color: #f2f2f2; color: #333; font-weight: bold; }}
                    .param-table tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    .strehl {{ font-size: 18px; color: #2E5A88; font-weight: bold; margin: 15px 0; }}
                    .quality {{ font-size: 16px; color: {quality_color}; font-weight: bold; margin: 10px 0; }}
                    .image-container {{ text-align: center; margin: 20px 0; }}
                    .image-container img {{ max-width: 100%; height: auto; border: 1px solid #ddd; }}
                    .university-header {{ background-color: #2E5A88; color: white; padding: 10px 20px; border-radius: 5px 5px 0 0; margin: -40px -40px 20px -40px; }}
                    .university-header h2 {{ margin: 0; font-size: 18px; }}
                    .lab-info {{ text-align: center; margin-bottom: 20px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="report">
                    <div class="university-header">
                        <h2>Университет ИТМО | Лабораторная работа №3 | {datetime.now().strftime('%d.%m.%Y')}</h2>
                    </div>
                    
                    <div class="header">
                        <h1 class="title">ОТЧЕТ О РАСЧЕТЕ ФРТ</h1>
                        <div class="date">Дата выполнения: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</div>
                    </div>
                    
                    <div class="section">
                        <h2 class="section-title">1. ПАРАМЕТРЫ РАСЧЕТА</h2>
                        
                        <h3 class="subsection-title">Основные параметры:</h3>
                        <table class="param-table">
                            <tr>
                                <th>Параметр</th>
                                <th>Значение</th>
                                <th>Единицы измерения</th>
                            </tr>
                            <tr><td>Размер (точек)</td><td>{params.size}</td><td>шт</td></tr>
                            <tr><td>Длина волны</td><td>{params.wavelength:.3f}</td><td>мкм</td></tr>
                            <tr><td>Задняя апертура</td><td>{params.back_aperture:.3f}</td><td></td></tr>
                            <tr><td>Увеличение</td><td>{params.magnification:.1f}</td><td></td></tr>
                            <tr><td>Расфокусировка</td><td>{params.defocus:.3f}</td><td>волн</td></tr>
                            <tr><td>Астигматизм</td><td>{params.astigmatism:.3f}</td><td>волн</td></tr>
                            <tr><td>Охват зрачка</td><td>{params.pupil_diameter:.3f}</td><td>к.ед.</td></tr>
                            <tr><td>Шаг по зрачку</td><td>{params.step_pupil:.6f}</td><td>к.ед.</td></tr>
                            <tr><td>Шаг по предмету</td><td>{params.step_object:.6f}</td><td>к.ед.</td></tr>
                            <tr><td>Шаг по изображению</td><td>{params.step_image:.6f}</td><td>к.ед.</td></tr>
                            <tr><td>Шаг в изображении</td><td>{step_microns:.6f}</td><td>мкм</td></tr>
                        </table>
                    </div>
                    
                    <div class="section">
                        <h2 class="section-title">2. РЕЗУЛЬТАТЫ РАСЧЕТА</h2>
                        <div class="strehl">Число Штреля: {strehl_ratio:.6f}</div>
                        <div class="quality">Качество системы: {quality}</div>
                    </div>
                    
                    <div class="section">
                        <h2 class="section-title">3. ГРАФИЧЕСКИЕ РЕЗУЛЬТАТЫ</h2>
                        <div class="image-container">
                            <p><em>В PDF версии отчета будут отображены графики ФРТ и сечений</em></p>
                        </div>
                    </div>
                    
                    <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; text-align: center;">
                        <p>Отчет сгенерирован автоматически</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return html_content
            
        except Exception as e:
            print(f"Ошибка создания предпросмотра: {e}")
            return f"<html><body><h1>Ошибка создания предпросмотра: {str(e)}</h1></body></html>"