from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="psf-calculator",
    version="1.0.0",
    author="Gushchin Daniil",
    author_email="gushchin.danya02@mail.ru",
    description="Программа для расчета функции рассеяния точки (ФРТ) с графическим интерфейсом",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Danya-Gushchin/user_psf_interface_itmo",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "psf-calculator=main:main",
        ],
    },
    include_package_data=True,
)