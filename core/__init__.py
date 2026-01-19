"""
Модуль core содержит основные классы для вычисления ФРТ.
"""

from .psf_params import ParamPSF
from .psf_calculator import PSFCalculator
from .fft_calculator import FFT

# Можно также определить, что импортируется при использовании from core import *
__all__ = [
    'ParamPSF',
    'PSFCalculator',
    'FFT'
]

print(f"Импортирован модуль core (версия 1.0)")