import numpy as np
from typing import Optional, Tuple
from core.psf_params import ParamPSF

class PSFCalculator:
    def __init__(self):
        self.last_pupil: Optional[np.ndarray] = None
        self.last_params: Optional[ParamPSF] = None
        self._step_im_microns: float = 0.0
        self.last_psf: Optional[np.ndarray] = None
        self.strehl_ratio: float = 0.0

    def compute(self, params: ParamPSF) -> Tuple[np.ndarray, float]:
        size = params.size

        # Вычисляем параметры дискретизации
        step_pupil = params.pupil_diameter / size
        step_obj_can = 1.0 / (step_pupil * size)
        
        self.last_params = params
        self._step_im_microns = step_obj_can * params.wavelength / (params.magnification * params.back_aperture)

        # Вычисляем функцию зрачка
        pupil = self._calc_pupil_function(
            size,
            step_pupil,
            params.defocus,
            params.astigmatism
        )
        self.last_pupil = pupil.copy()

        # Преобразование Фурье
        pupil_shifted = np.fft.ifftshift(pupil)
        field = np.fft.ifft2(pupil_shifted)
        field = np.fft.fftshift(field)

        # Масштабирование
        field *= (step_pupil / step_obj_can)

        # Интенсивность и нормализация
        intensity = np.abs(field) ** 2
        energy = np.sum(intensity)

        if energy > 0:
            psf = intensity / energy
        else:
            psf = intensity
            
        self.last_psf = psf
        
        # Вычисляем число Штреля
        self.strehl_ratio = self._calculate_strehl_ratio(psf)
        
        return psf, self.strehl_ratio

    def _calc_pupil_function(self, size, step_pupil, defocus, astigmatism):
        # Создаем координатную сетку
        x = np.arange(size) - size // 2
        y = np.arange(size) - size // 2
        X, Y = np.meshgrid(x, y)
        
        # Нормированные координаты
        X_norm = X * step_pupil
        Y_norm = Y * step_pupil
        
        # Радиальная и угловая координаты
        rho2 = X_norm**2 + Y_norm**2
        phi = np.arctan2(Y_norm, X_norm)

        # Апертурная функция (круглая апертура)
        mask = rho2 <= 1.0

        # Волновая аберрация
        W = 2.0 * np.pi * (
            defocus * (2.0 * rho2 - 1.0) +
            astigmatism * rho2 * np.cos(2.0 * phi)
        )

        return np.exp(1j * W) * mask

    def _calculate_strehl_ratio(self, psf: np.ndarray) -> float:
        """Вычисление числа Штреля как отношение максимальной интенсивности к идеальной"""
        if psf is None or len(psf) == 0:
            return 0.0
            
        # Для идеальной системы (без аберраций) максимальная интенсивность в центре
        # В нашем случае нормализованная PSF уже имеет сумму = 1
        # Число Штреля - это просто максимальное значение
        max_intensity = np.max(psf)
        
        # Для идеальной дифракционно-ограниченной системы 
        # максимальное значение PSF в центре примерно 1/(π*N^2) где N - размер
        # но так как мы нормализовали, то идеальное значение = 1
        ideal_max = 1.0
        
        return min(max_intensity / ideal_max, 1.0)