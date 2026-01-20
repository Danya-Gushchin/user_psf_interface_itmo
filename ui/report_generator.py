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
import matplotlib
matplotlib.use('Agg')  # Для работы без GUI


class ReportGenerator:
    """Генератор отчетов для печати результатов вычислений"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
        
    def _create_custom_styles(self):
        """Создание пользовательских стилей"""
        # Заголовок отчета
        if 'ReportTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='ReportTitle',
                parent=self.styles['Title'],
                fontSize=16,
                spaceAfter=30,
                alignment=TA_CENTER
            ))
        
        # Заголовок раздела
        if 'SectionTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SectionTitle',
                parent=self.styles['Heading1'],
                fontSize=14,
                spaceAfter=12,
                spaceBefore=20,
                textColor=colors.HexColor('#2E5A88')
            ))
        
        # Подзаголовок
        if 'SubTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SubTitle',
                parent=self.styles['Heading2'],
                fontSize=12,
                spaceAfter=8,
                spaceBefore=15,
                textColor=colors.HexColor('#444444')
            ))
        
        # Основной текст (используем другое имя)
        if 'ReportBodyText' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='ReportBodyText',
                parent=self.styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                leading=14
            ))
        
        # Текст лога
        if 'LogText' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='LogText',
                parent=self.styles['Code'],
                fontSize=8,
                spaceAfter=4,
                leading=10,
                fontName='Courier'
            ))
        
        # Параметр
        if 'ParamName' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='ParamName',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#2E5A88'),
                leftIndent=20
            ))
        
        # Значение параметра
        if 'ParamValue' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='ParamValue',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#000000'),
                leftIndent=40
            ))
    
    def generate_report(self, params, psf_data, strehl_ratio, step_microns, log_text, filename):
        """Сгенерировать PDF отчет"""
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        
        # Заголовок отчета
        story.append(Paragraph("ОТЧЕТ О РАСЧЕТЕ ФРТ", self.styles['ReportTitle']))
        story.append(Paragraph(f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}", 
                              self.styles['ReportBodyText']))
        story.append(Spacer(1, 20))
        
        # Раздел 1: Параметры расчета
        story.append(Paragraph("1. ПАРАМЕТРЫ РАСЧЕТА", self.styles['SectionTitle']))
        
        # Основные параметры
        story.append(Paragraph("Основные параметры:", self.styles['SubTitle']))
        
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
        
        params_table = Table(params_table_data, colWidths=[4*cm, 3*cm, 3*cm])
        params_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8E8E8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#000000')),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F8F8')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#000000')),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#C0C0C0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(params_table)
        story.append(Spacer(1, 20))
        
        # Раздел 2: Результаты
        story.append(Paragraph("2. РЕЗУЛЬТАТЫ РАСЧЕТА", self.styles['SectionTitle']))
        
        # Число Штреля
        story.append(Paragraph(f"Число Штреля: <b>{strehl_ratio:.6f}</b>", self.styles['ReportBodyText']))
        
        quality = "Отличное" if strehl_ratio > 0.8 else "Хорошее" if strehl_ratio > 0.6 else "Удовлетворительное" if strehl_ratio > 0.4 else "Плохое"
        story.append(Paragraph(f"Качество системы: <b>{quality}</b>", self.styles['ReportBodyText']))
        story.append(Spacer(1, 15))
        
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
        
        # Раздел 4: Лог вычислений
        if log_text:
            story.append(Paragraph("4. ЛОГ ВЫЧИСЛЕНИЙ", self.styles['SectionTitle']))
            
            # Ограничиваем длину лога для отчета
            max_log_lines = 50
            log_lines = log_text.split('\n')
            if len(log_lines) > max_log_lines:
                log_lines = log_lines[-max_log_lines:]
                log_text_short = '\n'.join(log_lines)
                story.append(Paragraph(f"(показаны последние {max_log_lines} строк)", self.styles['ReportBodyText']))
            else:
                log_text_short = log_text
            
            # Добавляем лог в таблице для лучшего форматирования
            log_table_data = [[Paragraph(line.replace('\t', '    '), self.styles['LogText'])] 
                             for line in log_text_short.split('\n') if line.strip()]
            
            if log_table_data:
                log_table = Table(log_table_data, colWidths=[14*cm])
                log_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0F0F0')),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Courier'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#C0C0C0')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(log_table)
        
        # Раздел 5: Заключение
        story.append(Paragraph("5. ЗАКЛЮЧЕНИЕ", self.styles['SectionTitle']))
        
        conclusion_text = f"""
        Расчет функции рассеяния точки (ФРТ) выполнен с заданными параметрами. 
        Система демонстрирует {quality.lower()} качество формирования изображения 
        с числом Штреля {strehl_ratio:.4f}. 
        """
        
        if params.defocus != 0 or params.astigmatism != 0:
            conclusion_text += "Наличие аберраций влияет на качество изображения. "
        
        if strehl_ratio < 0.8:
            conclusion_text += "Рекомендуется оптимизировать параметры системы для улучшения качества."
        else:
            conclusion_text += "Система работает вблизи дифракционного предела."
        
        story.append(Paragraph(conclusion_text, self.styles['ReportBodyText']))
        story.append(Spacer(1, 20))
        
        # Подпись
        story.append(Paragraph("_________________________", self.styles['ReportBodyText']))
        story.append(Paragraph("Подпись", self.styles['ReportBodyText']))
        
        # Строим PDF
        doc.build(story)
        
        return True
    
    def _create_psf_image(self, psf_data, strehl_ratio):
        """Создать изображение PSF для отчета"""
        try:
            # Создаем фигуру
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Отображаем PSF
            im = ax.imshow(psf_data, cmap='inferno', aspect='auto')
            ax.set_title(f'Функция рассеяния точки\nЧисло Штреля: {strehl_ratio:.4f}', fontsize=12)
            ax.set_xlabel('Координата X, пиксели', fontsize=10)
            ax.set_ylabel('Координата Y, пиксели', fontsize=10)
            
            # Добавляем цветовую шкалу
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('Интенсивность', fontsize=10)
            
            # Сохраняем в буфер
            buf = io.BytesIO()
            plt.tight_layout()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            buf.seek(0)
            return Image(buf, width=14*cm, height=10*cm)
            
        except Exception as e:
            print(f"Ошибка создания изображения PSF: {e}")
            return Paragraph(f"Не удалось создать изображение ФРТ: {str(e)}", self.styles['ReportBodyText'])
    
    def _create_slices_image(self, psf_data):
        """Создать изображение сечений PSF для отчета"""
        try:
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
            return Paragraph(f"Не удалось создать сечения ФРТ: {str(e)}", self.styles['ReportBodyText'])
    
    def generate_preview(self, params, psf_data, strehl_ratio, step_microns, log_text):
        """Сгенерировать HTML предпросмотр отчета"""
        try:
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
                    .log {{ background-color: #f8f8f8; border: 1px solid #ddd; padding: 15px; font-family: monospace; font-size: 12px; 
                           max-height: 300px; overflow-y: auto; white-space: pre-wrap; }}
                    .conclusion {{ background-color: #e8f4f8; border-left: 4px solid #2E5A88; padding: 15px; margin-top: 20px; }}
                    .image-container {{ text-align: center; margin: 20px 0; }}
                    .image-container img {{ max-width: 100%; height: auto; border: 1px solid #ddd; }}
                </style>
            </head>
            <body>
                <div class="report">
                    <div class="header">
                        <h1 class="title">ОТЧЕТ О РАСЧЕТЕ ФРТ</h1>
                        <div class="date">Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</div>
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
            """
            
            # Определяем качество
            quality = "Отличное" if strehl_ratio > 0.8 else "Хорошее" if strehl_ratio > 0.6 else "Удовлетворительное" if strehl_ratio > 0.4 else "Плохое"
            html_content += f'<p><strong>Качество системы:</strong> {quality}</p>'
            
            # Добавляем графики (заглушки - в реальности нужно вставить base64 изображения)
            html_content += """
                    </div>
                    
                    <div class="section">
                        <h2 class="section-title">3. ГРАФИЧЕСКИЕ РЕЗУЛЬТАТЫ</h2>
                        <div class="image-container">
                            <p><em>В PDF версии отчета будут отображены графики ФРТ и сечений</em></p>
                        </div>
                    </div>
            """
            
            # Лог вычислений
            if log_text:
                html_content += """
                    <div class="section">
                        <h2 class="section-title">4. ЛОГ ВЫЧИСЛЕНИЙ</h2>
                        <div class="log">
                """
                
                # Ограничиваем длину лога
                max_log_lines = 30
                log_lines = log_text.split('\n')
                if len(log_lines) > max_log_lines:
                    log_lines = log_lines[-max_log_lines:]
                    html_content += f"<em>(показаны последние {max_log_lines} строк)</em><br><br>"
                
                for line in log_lines:
                    if line.strip():
                        html_content += f"{line.replace(' ', '&nbsp;').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')}<br>"
                
                html_content += """
                        </div>
                    </div>
                """
            
            # Заключение
            conclusion_text = f"""
            Расчет функции рассеяния точки (ФРТ) выполнен с заданными параметрами. 
            Система демонстрирует {quality.lower()} качество формирования изображения 
            с числом Штреля {strehl_ratio:.4f}. 
            """
            
            if params.defocus != 0 or params.astigmatism != 0:
                conclusion_text += "Наличие аберраций влияет на качество изображения. "
            
            if strehl_ratio < 0.8:
                conclusion_text += "Рекомендуется оптимизировать параметры системы для улучшения качества."
            else:
                conclusion_text += "Система работает вблизи дифракционного предела."
            
            html_content += f"""
                    <div class="section">
                        <h2 class="section-title">5. ЗАКЛЮЧЕНИЕ</h2>
                        <div class="conclusion">
                            {conclusion_text}
                        </div>
                    </div>
                    
                    <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: right;">
                        <p>_________________________</p>
                        <p><em>Подпись</em></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return html_content
            
        except Exception as e:
            print(f"Ошибка создания предпросмотра: {e}")
            return f"<html><body><h1>Ошибка создания предпросмотра: {str(e)}</h1></body></html>"