import os

from setuptools import find_packages, setup

PROJECT_DIR = os.path.dirname(__file__)


setup(
    name="zelthy_enterprise",
    version="0.1",
    description="Zelthy3 AppDev Framework",
    author='Zelthy ("Healthlane Technologies")',
    author_email="platform@zelthy.com",
    package_dir={"": "src"},
    packages=find_packages("src"),
    include_package_data=True,
)
