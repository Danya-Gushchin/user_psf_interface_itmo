import numpy as np
from typing import Optional
from core.psf_params import ParamPSF


class PSFCalculator:

    def __init__(self):
        self.last_pupil: Optional[np.ndarray] = None
        self.last_params: Optional[ParamPSF] = None
        self._step_im_microns: float = 0.0

    def compute(self, params: ParamPSF) -> np.ndarray:
        size = params.size

        aperture = params.magnification * params.back_aperture
        step_pupil = params.pupil_diameter / size

        step_obj_can = 1.0 / (step_pupil * size)
        step_im_can = step_obj_can

        self.last_params = params
        self._step_im_microns = step_im_can * params.wavelength / params.back_aperture

        pupil = self._calc_pupil_function(
            size,
            step_pupil,
            params.defocus,
            params.astigmatism
        )
        self.last_pupil = pupil.copy()

        pupil = np.fft.ifftshift(pupil)
        field = np.fft.ifft2(pupil)
        field = np.fft.fftshift(field)

        field *= (step_pupil / step_obj_can)

        intensity = np.abs(field) ** 2
        energy = np.sum(intensity)

        return intensity / energy if energy > 0 else intensity

    def _calc_pupil_function(self, size, step_pupil, defocus, astigmatism):
        idx = np.arange(size)
        coords = (idx - size // 2) * step_pupil
        X, Y = np.meshgrid(coords, coords)

        rho2 = X**2 + Y**2
        phi = np.arctan2(X, Y)

        mask = rho2 <= 1.0

        W = 2.0 * np.pi * (
            defocus * (2.0 * rho2 - 1.0) +
            astigmatism * rho2 * np.cos(2.0 * phi)
        )

        return np.exp(1j * W) * mask
