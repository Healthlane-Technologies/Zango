import os
from setuptools import setup, find_packages
from pathlib import Path


PROJECT_DIR = os.path.dirname(__file__)
REQUIREMENTS_DIR = os.path.join(PROJECT_DIR, "requirements")

README = os.path.join(Path(__file__).resolve().parent.parent, "README.md")

PLATFORM_VERSION = "0.0.1rc"


def get_requirements(env):
    with open(os.path.join(REQUIREMENTS_DIR, f"{env}.txt")) as fp:
        return [x.strip() for x in fp.read().split("\n") if not x.startswith("#")]


install_requires = get_requirements("base")


setup(
    name="zelthy3",
    version=PLATFORM_VERSION,
    license='Apache License 2.0',
    description="Zelthy3: multi-tenant Django framework for building business apps",
    long_description=open(README).read(),
    long_description_content_type="text/markdown",
    author='Zelthy ("Healthlane Technologies")',
    author_email="maintainers@zelthy.com",
    url="https://github.com/Healthlane-Technologies/zelthy3",
    package_dir={"": "src"},
    packages=find_packages("src"),
    package_data={
        "zelthy": [
            "cli/project_template/**/*",
            "assets/**",
            "**/templates/**",
            "**/workspace_folder_template/**",
        ],
    },
    install_requires=install_requires,
    classifiers=[
        "Framework :: Django",
        "Programming Language :: Python",
    ],
    entry_points={
        "console_scripts": [
            "zelthy3=zelthy.cli:cli",
        ],
    },
    license_files=["LICENSE"]
)