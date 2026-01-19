import numpy as np
from typing import Optional, Tuple
from core.psf_params import ParamPSF
from core.fft_calculator import FFT

class PSFCalculator:
    def __init__(self):
        self.last_pupil: Optional[np.ndarray] = None
        self.last_params: Optional[ParamPSF] = None
        self._step_im_microns: float = 0.0
        self.last_psf: Optional[np.ndarray] = None
        self.strehl_ratio: float = 0.0

    def compute(self, params: ParamPSF) -> Tuple[np.ndarray, float]:
        size = params.size

        aperture = params.magnification * params.back_aperture
        step_pupil = params.pupil_diameter / size

        step_obj_can = 1.0 / (step_pupil * size)
        step_im_can = step_obj_can

        self.last_params = params
        self._step_im_microns = step_im_can * params.wavelength / aperture

        pupil = self._calc_pupil_function(
            size,
            step_pupil,
            params.defocus,
            params.astigmatism
        )
        self.last_pupil = pupil.copy()

        pupil = FFT.ifftshift(pupil)
        field = FFT.ifft2(pupil)
        field = FFT.fftshift(field)

        field *= (step_pupil / step_obj_can)

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

    def _calc_pupil_function(self, size, step_pupil, defocus, astigmatism):
        idx = np.arange(size)
        coords = (idx - size // 2) * step_pupil
        X, Y = np.meshgrid(coords, coords)

        rho2 = X**2 + Y**2
        phi = np.arctan2(Y, X)  # Исправлено: Y, X вместо X, Y

        mask = rho2 <= 1.0

        W = 2.0 * np.pi * (
            defocus * (2.0 * rho2 - 1.0) +
            astigmatism * rho2 * np.cos(2.0 * phi)
        )

        return np.exp(1j * W) * mask

    def _calculate_strehl_ratio(self, psf: np.ndarray, params: ParamPSF) -> float:
        """Вычисление числа Штреля"""
        if self.last_pupil is None:
            return 0.0
            
        ideal_pupil = np.ones_like(self.last_pupil) * (np.abs(self.last_pupil) > 0)
        ideal_field = FFT.ifft2(FFT.ifftshift(ideal_pupil))
        ideal_field = FFT.fftshift(ideal_field)
        ideal_intensity = np.abs(ideal_field) ** 2
        ideal_energy = np.sum(ideal_intensity)
        
        if ideal_energy > 0:
            ideal_psf = ideal_intensity / ideal_energy
        else:
            ideal_psf = ideal_intensity
            
        max_actual = np.max(psf)
        max_ideal = np.max(ideal_psf)
        
        return max_actual / max_ideal if max_ideal > 0 else 0.0

    def get_x_slice(self, psf: np.ndarray) -> np.ndarray:
        """Получить сечение по X (горизонтальное)"""
        if psf is None or psf.shape[0] == 0:
            return np.array([])
        center = psf.shape[0] // 2
        return psf[center, :]

    def get_y_slice(self, psf: np.ndarray) -> np.ndarray:
        """Получить сечение по Y (вертикальное)"""
        if psf is None or psf.shape[0] == 0:
            return np.array([])
        center = psf.shape[1] // 2
        return psf[:, center]

    def get_coordinates(self, psf: np.ndarray, in_microns: bool = False) -> Tuple[np.ndarray, np.ndarray]:
        """Получить координаты для графиков"""
        size = psf.shape[0]
        
        if in_microns and self._step_im_microns > 0:
            extent = size * self._step_im_microns / 2
            x_coords = np.linspace(-extent, extent, size)
            y_coords = np.linspace(-extent, extent, size)
            unit = "мкм"
        else:
            x_coords = np.arange(size) - size // 2
            y_coords = np.arange(size) - size // 2
            unit = "пиксели"
            
        return x_coords, y_coords, unit