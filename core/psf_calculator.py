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
        step_pupil = params.step_pupil
        step_obj_can = params.step_object
        
        self.last_params = params
        self._step_im_microns = step_obj_can * params.wavelength / (params.magnification * params.back_aperture)

        # Вычисляем функцию зрачка С УЧЕТОМ ВСЕХ ПАРАМЕТРОВ
        pupil = self._calc_pupil_function(
            size,
            step_pupil,
            params.wavelength,      # Добавляем длину волны
            params.back_aperture,   # Добавляем апертуру
            params.defocus,
            params.astigmatism
        )
        self.last_pupil = pupil.copy()

        # Преобразование Фурье
        pupil_shifted = np.fft.ifftshift(pupil)
        field = np.fft.ifft2(pupil_shifted)
        field = np.fft.fftshift(field)

        # Масштабирование с учетом увеличения
        # Для системы с увеличением M: координаты в изображении = координаты в каустике / M
        field *= (step_pupil / step_obj_can) / params.magnification

        # Интенсивность и нормализация
        intensity = np.abs(field) ** 2
        energy = np.sum(intensity)

        if energy > 0:
            psf = intensity / energy
        else:
            psf = intensity
            
        self.last_psf = psf
        
        # Вычисляем число Штреля
        self.strehl_ratio = self._calculate_strehl_ratio(psf, params)
        
        return psf, self.strehl_ratio

    def _calc_pupil_function(self, size, step_pupil, wavelength, back_aperture, defocus, astigmatism):
        """Вычисление функции зрачка с учетом всех параметров"""
        # Создаем координатную сетку
        x = np.arange(size) - size // 2
        y = np.arange(size) - size // 2
        X, Y = np.meshgrid(x, y)
        
        # Нормированные координаты (в единицах длины волны)
        # Масштабируем на длину волны для правильного дифракционного предела
        X_norm = X * step_pupil / wavelength
        Y_norm = Y * step_pupil / wavelength
        
        # Радиальная и угловая координаты
        rho2 = X_norm**2 + Y_norm**2
        rho = np.sqrt(rho2)
        phi = np.arctan2(Y_norm, X_norm)

        # Апертурная функция (круглая апертура)
        # back_aperture - числовая апертура NA
        # В нормированных координатах радиус апертуры = NA / λ
        aperture_radius = back_aperture / wavelength
        mask = rho <= aperture_radius

        # Волновая аберрация в единицах длины волны
        # Масштабируем на квадрат радиуса для правильных единиц
        norm_factor = (aperture_radius**2) if aperture_radius > 0 else 1.0
        
        # Defocus: W = defocus * (2 * (ρ/a)^2 - 1)
        # где a = aperture_radius
        W_defocus = defocus * (2.0 * (rho2 / norm_factor) - 1.0) if norm_factor > 0 else 0
        
        # Astigmatism: W = astigmatism * (ρ/a)^2 * cos(2*φ)
        W_astigmatism = astigmatism * (rho2 / norm_factor) * np.cos(2.0 * phi) if norm_factor > 0 else 0
        
        W = W_defocus + W_astigmatism
        
        # Конвертируем в фазу (2π * W)
        phase = 2.0 * np.pi * W

        # Функция зрачка: амплитуда * exp(i*фаза)
        pupil_function = np.zeros_like(rho, dtype=complex)
        pupil_function[mask] = np.exp(1j * phase[mask])
        
        # Нормализуем энергию
        energy = np.sum(np.abs(pupil_function[mask])**2)
        if energy > 0:
            pupil_function[mask] /= np.sqrt(energy / np.sum(mask))
        
        return pupil_function

    def _calculate_strehl_ratio(self, psf: np.ndarray, params: ParamPSF) -> float:
        """Вычисление числа Штреля с учетом параметров системы"""
        if psf is None or len(psf) == 0:
            return 0.0
            
        # Максимальная интенсивность в центре
        size = psf.shape[0]
        center = size // 2
        
        # Берем небольшую область в центре
        x_slice = slice(max(0, center-2), min(size, center+3))
        y_slice = slice(max(0, center-2), min(size, center+3))
        central_region = psf[x_slice, y_slice]
        
        # Среднее значение в центральной области
        max_intensity = np.mean(central_region) if central_region.size > 0 else 0
        
        # Для идеальной системы с круглой апертурой
        # Интенсивность в центре Airy диска: I0 = (π * NA^2 / λ)^2
        # Где NA = back_aperture
        if params.wavelength > 0 and params.back_aperture > 0:
            ideal_intensity = (np.pi * params.back_aperture**2 / params.wavelength)**2
        else:
            ideal_intensity = 1.0
        
        # Нормализуем на общую энергию
        total_energy = np.sum(psf)
        if total_energy > 0:
            max_intensity_normalized = max_intensity / total_energy
            ideal_intensity_normalized = ideal_intensity / (ideal_intensity * np.pi * (params.back_aperture/params.wavelength)**2) if ideal_intensity > 0 else 1.0
            
            strehl = max_intensity_normalized / ideal_intensity_normalized if ideal_intensity_normalized > 0 else 0.0
        else:
            strehl = 0.0
        
        # Ограничиваем значения [0, 1]
        return max(0.0, min(strehl, 1.0))