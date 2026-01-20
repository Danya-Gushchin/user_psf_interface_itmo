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
        
        # Вычисляем шаг в микронах (физический размер пикселя)
        # В пространстве изображения: размер пикселя = (шаг в пространстве предмета) * увеличение
        self._step_im_microns = step_obj_can * params.magnification

        # Вычисляем функцию зрачка С ПРАВИЛЬНЫМ УЧЕТОМ ВСЕХ ПАРАМЕТРОВ
        pupil = self._calc_pupil_function(
            size=size,
            step_pupil=step_pupil,
            wavelength=params.wavelength,
            back_aperture=params.back_aperture,
            defocus=params.defocus,
            astigmatism=params.astigmatism
        )
        self.last_pupil = pupil.copy()

        # Преобразование Фурье
        pupil_shifted = np.fft.ifftshift(pupil)
        field = np.fft.ifft2(pupil_shifted)
        field = np.fft.fftshift(field)

        # Масштабирование: учитываем физический смысл преобразования
        # field уже представляет распределение поля в фокальной плоскости
        # Нормировочный коэффициент для правильных единиц
        field *= (step_pupil / step_obj_can)

        # Интенсивность
        intensity = np.abs(field) ** 2
        
        # Нормализация (сумма интенсивностей = 1)
        total_intensity = np.sum(intensity)
        if total_intensity > 0:
            psf = intensity / total_intensity
        else:
            psf = intensity
            
        self.last_psf = psf
        
        # Вычисляем число Штреля
        self.strehl_ratio = self._calculate_strehl_ratio(psf, params)
        
        return psf, self.strehl_ratio

    def _calc_pupil_function(self, size, step_pupil, wavelength, back_aperture, defocus, astigmatism):
        """
        Вычисление функции зрачка с правильным учетом всех параметров
        
        Ключевые моменты:
        1. Длина волны влияет на масштаб дифракции
        2. Апертура определяет радиус апертуры
        3. Defocus и astigmatism - аберрации в единицах длин волн
        """
        # Создаем координатную сетку в плоскости зрачка
        x = np.arange(size) - size // 2
        y = np.arange(size) - size // 2
        X, Y = np.meshgrid(x, y)
        
        # Координаты в единицах длины волны (важно для дифракции!)
        # Нормируем на длину волны: координаты в единицах λ
        X_norm = X * step_pupil / wavelength if wavelength > 0 else X * step_pupil
        Y_norm = Y * step_pupil / wavelength if wavelength > 0 else Y * step_pupil
        
        # Радиальная координата (в единицах λ)
        rho = np.sqrt(X_norm**2 + Y_norm**2)
        
        # Угловая координата
        phi = np.arctan2(Y_norm, X_norm)
        
        # Функция апертуры (круглая апертура)
        # Радиус апертуры в нормированных координатах: NA / λ
        # Где NA = back_aperture (числовая апертура)
        if wavelength > 0:
            aperture_radius_norm = back_aperture / wavelength
        else:
            aperture_radius_norm = back_aperture / 0.555  # по умолчанию для зеленого света
        
        mask = rho <= aperture_radius_norm
        
        # Нормированный радиус внутри апертуры (от 0 до 1)
        rho_norm = np.zeros_like(rho)
        if aperture_radius_norm > 0:
            rho_norm[mask] = rho[mask] / aperture_radius_norm
        
        # ВОЛНОВАЯ АБЕРРАЦИЯ (в единицах длин волн)
        # Это то, что ДОЛЖНО зависеть от длины волны через ρ_norm
        W = np.zeros_like(rho)
        
        # Defocus: W = defocus * (2 * ρ^2 - 1)
        # Astigmatism: W = astigmatism * ρ^2 * cos(2φ)
        if np.any(mask):
            W[mask] = (defocus * (2.0 * rho_norm[mask]**2 - 1.0) + 
                      astigmatism * rho_norm[mask]**2 * np.cos(2.0 * phi[mask]))
        
        # Фазовая задержка (в радианах) = 2π * W
        phase = 2.0 * np.pi * W
        
        # Функция зрачка: 1 внутри апертуры, 0 вне, с фазовым множителем
        pupil = np.zeros((size, size), dtype=complex)
        pupil[mask] = np.exp(1j * phase[mask])
        
        return pupil
    
    def _calculate_strehl_ratio(self, psf: np.ndarray, params: ParamPSF) -> float:
        """Вычисление числа Штреля"""
        if psf is None or psf.size == 0:
            return 0.0
        
        # Центр PSF
        center_y, center_x = psf.shape[0] // 2, psf.shape[1] // 2
        
        # Максимальная интенсивность в центре (область 3x3)
        y_start = max(0, center_y - 1)
        y_end = min(psf.shape[0], center_y + 2)
        x_start = max(0, center_x - 1)
        x_end = min(psf.shape[1], center_x + 2)
        
        central_region = psf[y_start:y_end, x_start:x_end]
        if central_region.size == 0:
            return 0.0
        
        max_intensity = np.mean(central_region)
        
        # Для идеальной системы (без аберраций) с круглой апертурой
        # Интенсивность в центре пропорциональна (π * (NA/λ)^2)^2
        if params.back_aperture > 0 and params.wavelength > 0:
            # Нормировочный коэффициент
            norm_factor = (np.pi * (params.back_aperture / params.wavelength)**2)
            ideal_intensity = norm_factor**2
        else:
            ideal_intensity = 1.0
        
        # Число Штреля = отношение реальной интенсивности к идеальной
        strehl = max_intensity / ideal_intensity if ideal_intensity > 0 else max_intensity
        
        # Ограничиваем значение [0, 1]
        return max(0.0, min(strehl, 1.0))