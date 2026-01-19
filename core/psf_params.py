from dataclasses import dataclass


@dataclass
class ParamPSF:
    size: int = 512
    wavelength: float = 0.555        # мкм
    back_aperture: float = 0.5
    magnification: float = 1.0
    defocus: float = 0.0
    astigmatism: float = 0.0

    # параметры дискретизации
    pupil_diameter: float = 8.0      # к.ед.
    step_pupil: float = 0.0625       # к.ед.
    step_object: float = 0.13875     # к.ед.
    step_image: float = 0.13875      # к.ед.
