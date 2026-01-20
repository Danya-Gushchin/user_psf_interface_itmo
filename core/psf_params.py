from dataclasses import dataclass


@dataclass
class ParamPSF:
    size: int = 512
    wavelength: float = 0.555        # мкм
    back_aperture: float = 0.5       # Числовая апертура NA
    magnification: float = 1.0
    defocus: float = 0.0            # в длинах волн λ
    astigmatism: float = 0.0        # в длинах волн λ

    # параметры дискретизации
    pupil_diameter: float = 8.0      # к.ед.
    step_pupil: float = 0.0625       # к.ед.
    step_object: float = 0.13875     # к.ед.
    step_image: float = 0.13875      # к.ед.
    
    def calculate_step_microns(self) -> float:
        """Вычислить шаг в микронах в плоскости изображения"""
        if self.step_image > 0 and self.wavelength > 0 and self.back_aperture > 0:
            # Для дифракционно-ограниченной системы:
            # Разрешение по Рэлею: δ = 0.61 * λ / NA
            # Шаг дискретизации должен быть меньше δ/2 (критерий Найквиста)
            rayleigh_resolution = 0.61 * self.wavelength / self.back_aperture
            # Шаг в изображении с учетом увеличения
            step_in_object_space = self.step_image
            step_in_image_space = step_in_object_space * self.magnification
            return step_in_image_space
        return 0.0
    
    def calculate_airy_disk_radius(self) -> float:
        """Вычислить радиус Airy диска в микронах"""
        if self.wavelength > 0 and self.back_aperture > 0:
            # Радиус первого нуля Airy диска: 1.22 * λ / NA
            return 1.22 * self.wavelength / self.back_aperture
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