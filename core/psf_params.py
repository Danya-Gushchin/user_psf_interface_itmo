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
    
    def calculate_step_microns(self) -> float:
        """Вычислить шаг в микронах"""
        if self.step_object > 0 and self.wavelength > 0:
            return self.step_object * self.wavelength / (self.magnification * self.back_aperture)
        return 0.0
    
    def recalculate_from_pupil_diameter(self):
        """Пересчитать шаги на основе охвата зрачка"""
        if self.size > 0:
            self.step_pupil = self.pupil_diameter / self.size
            if self.step_pupil > 0:
                self.step_object = 1.0 / (self.step_pupil * self.size)
                self.step_image = self.step_object
    
    def recalculate_from_step_pupil(self):
        """Пересчитать на основе шага по зрачку"""
        if self.step_pupil > 0:
            self.pupil_diameter = self.step_pupil * self.size
            if self.size > 0:
                self.step_object = 1.0 / (self.step_pupil * self.size)
                self.step_image = self.step_object
    
    def recalculate_from_step_object(self):
        """Пересчитать на основе шага по предмету"""
        if self.step_object > 0 and self.size > 0:
            self.step_image = self.step_object
            self.step_pupil = 1.0 / (self.step_object * self.size)
            self.pupil_diameter = self.step_pupil * self.size
    
    def recalculate_from_step_image(self):
        """Пересчитать на основе шага по изображению"""
        if self.step_image > 0 and self.size > 0:
            self.step_object = self.step_image
            self.step_pupil = 1.0 / (self.step_image * self.size)
            self.pupil_diameter = self.step_pupil * self.size