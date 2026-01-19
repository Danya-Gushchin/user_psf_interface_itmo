import numpy as np
from typing import Tuple

class FFT:
    """Класс для выполнения преобразования Фурье"""
    
    @staticmethod
    def fft2(data: np.ndarray) -> np.ndarray:
        """2D прямое преобразование Фурье"""
        return np.fft.fft2(data)
    
    @staticmethod
    def ifft2(data: np.ndarray) -> np.ndarray:
        """2D обратное преобразование Фурье"""
        return np.fft.ifft2(data)
    
    @staticmethod
    def fftshift(data: np.ndarray) -> np.ndarray:
        """Сдвиг нулевой частоты в центр"""
        return np.fft.fftshift(data)
    
    @staticmethod
    def ifftshift(data: np.ndarray) -> np.ndarray:
        """Обратный сдвиг нулевой частоты"""
        return np.fft.ifftshift(data)