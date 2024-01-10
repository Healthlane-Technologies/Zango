import os
from setuptools import setup, find_packages


PROJECT_DIR = os.path.dirname(__file__)
REQUIREMENTS_DIR = os.path.join(PROJECT_DIR, "requirements")


def get_requirements(env):
    with open(os.path.join(REQUIREMENTS_DIR, f"{env}.txt")) as fp:
        return [x.strip() for x in fp.read().split("\n") if not x.startswith("#")]


install_requires = get_requirements("base")


setup(
    name="zelthy3",
    version="0.1",
    description="Zelthy3 AppDev Framework",
    author='Zelthy ("Healthlane Technologies")',
    author_email="platform@zelthy.com",
    url="https://github.com/Healthlane-Technologies/zelthy3",
    # packages=find_packages(),
    package_dir={"": "src"},
    packages=find_packages("src"),
    package_data={"zelthy": ["cli/project_template/**/*", "assets/**", "**/templates/**", "**/workspace_folder_template/**"],},
    install_requires=install_requires,
    classifiers=[
        "Framework :: Django",
        "Programming Language :: Python",
        # Other classifiers...
    ],
    entry_points={
        "console_scripts": [
            "zelthy3=zelthy.cli:cli",
        ],
    },
)
