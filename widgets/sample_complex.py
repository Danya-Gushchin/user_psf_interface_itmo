import numpy as np
from widgets.sample import Sample

class SampleComplex:
    """Класс для работы с комплексными выборками"""
    
    def __init__(self, data: np.ndarray, step: float = 1.0):
        self.data = data
        self.step = step
        self.size = data.shape[0] if len(data.shape) > 0 else 1
        
    def amplitude(self) -> Sample:
        """Получить амплитуду"""
        return Sample(np.abs(self.data), self.step)
    
    def phase(self) -> Sample:
        """Получить фазу"""
        return Sample(np.angle(self.data), self.step)
    
    def intensity(self) -> Sample:
        """Получить интенсивность"""
        return Sample(np.abs(self.data) ** 2, self.step)
    
    def get_coordinates(self) -> np.ndarray:
        """Получить координаты по оси"""
        center = self.size // 2
        return np.arange(-center, self.size - center) * self.step