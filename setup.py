"""setup"""

import re
from pathlib import Path
from setuptools import setup, find_packages


def get_version() -> str:
    # read version from file to prevet import error
    cwd = Path(__file__).parent
    # nearest __init__.py file
    init_path = next(cwd.glob("*/__init__.py"))
    pattern = re.compile(r'^__version__\ *=\ *"(\d+(\.\d+)+)"')
    with init_path.open() as file:
        while line := file.readline():
            if match := pattern.match(line):
                return match.group(1)
    raise ValueError("unable find version")


setup(
    name="python_tesseract",
    version=get_version(),
    description="Tesseract-ocr interface",
    author="Ginanjar Nuraeni",
    author_email="ginanjarn@gmail.com",
    license="MIT",
    packages=find_packages(),
    package_data={"": ["LICENSE"]},
    include_package_data=True,
    install_requires=[
        "pillow",
    ],
)
