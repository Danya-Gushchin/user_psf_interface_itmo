import numpy as np
import pandas as pd
from typing import List, Dict, Any
from dataclasses import asdict
from core.psf_params import ParamPSF


class TableUtils:
    """Утилиты для работы с таблицей параметров"""
    
    @staticmethod
    def params_to_dict(params: ParamPSF, strehl: float = 0.0) -> Dict[str, Any]:
        """Преобразование параметров в словарь для таблицы"""
        data = asdict(params)
        data['strehl_ratio'] = strehl
        return data
    
    @staticmethod
    def dict_to_params(data: Dict[str, Any]) -> ParamPSF:
        """Преобразование словаря в параметры"""
        # Копируем только нужные поля
        param_keys = [
            'size', 'wavelength', 'back_aperture', 'magnification',
            'defocus', 'astigmatism', 'pupil_diameter',
            'step_pupil', 'step_object', 'step_image'
        ]
        
        params_data = {k: data.get(k, 0) for k in param_keys}
        return ParamPSF(**params_data)
    
    @staticmethod
    def calculate_step_params(params: ParamPSF) -> ParamPSF:
        """Пересчет параметров дискретизации"""
        # Если задан охват зрачка, вычисляем шаг по зрачку
        if params.pupil_diameter > 0 and params.size > 0:
            params.step_pupil = params.pupil_diameter / params.size
        
        # Вычисляем шаг по объекту/изображению
        if params.step_pupil > 0 and params.size > 0:
            params.step_object = 1.0 / (params.step_pupil * params.size)
            params.step_image = params.step_object
        
        return params
    
    @staticmethod
    def export_table_to_clipboard(data_list: List[Dict]) -> str:
        """Экспорт таблицы в строку для буфера обмена"""
        if not data_list:
            return ""
        
        df = pd.DataFrame(data_list)
        return df.to_csv(index=False, sep='\t')
    
    @staticmethod
    def export_table_to_file(data_list: List[Dict], filename: str):
        """Экспорт таблицы в файл"""
        if not data_list:
            return
        
        df = pd.DataFrame(data_list)
        
        if filename.endswith('.csv'):
            df.to_csv(filename, index=False)
        elif filename.endswith('.txt'):
            df.to_csv(filename, index=False, sep='\t')
        elif filename.endswith('.xlsx'):
            df.to_excel(filename, index=False)
        else:
            # По умолчанию сохраняем как CSV
            df.to_csv(filename, index=False)
    
    @staticmethod
    def import_table_from_file(filename: str) -> List[Dict]:
        """Импорт таблицы из файла"""
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(filename)
            elif filename.endswith('.txt'):
                df = pd.read_csv(filename, sep='\t')
            elif filename.endswith('.xlsx'):
                df = pd.read_excel(filename)
            else:
                df = pd.read_csv(filename)  # пробуем по умолчанию
            
            return df.to_dict('records')
        except Exception as e:
            raise ValueError(f"Ошибка чтения файла: {str(e)}")