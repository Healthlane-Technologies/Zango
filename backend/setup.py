import os

from setuptools import find_packages, setup


PROJECT_DIR = os.path.dirname(__file__)
REQUIREMENTS_DIR = os.path.join(PROJECT_DIR, "requirements")
README = os.path.join(PROJECT_DIR, "README.md")

PLATFORM_VERSION = "1.0.4"


def get_requirements(env):
    requirements_file = os.path.join(REQUIREMENTS_DIR, f"{env}.txt")

    # Check if requirements file exists
    if not os.path.exists(requirements_file):
        return []

    with open(requirements_file, encoding="utf-8") as fp:
        install_requires = []

        for line in fp:
            line = line.strip()
            if line and not line.startswith("#"):
                if line.startswith("git+"):
                    # Convert git URL to PEP 508 format
                    if "@" in line:
                        repo_part, branch_part = line.split("@", 1)
                    else:
                        repo_part = line
                        branch_part = "main"

                    # Extract package name from git URL
                    package_name = repo_part.split("/")[-1].replace(".git", "")

                    # Clean package name (remove any query parameters)
                    if "?" in package_name:
                        package_name = package_name.split("?")[0]

                    # PEP 508 format: package_name @ git+url
                    pep508_url = f"{package_name} @ {line}"
                    install_requires.append(pep508_url)
                else:
                    install_requires.append(line)

        return install_requires


def get_long_description():
    """Safely read README file"""
    try:
        with open(README, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Zango: multi-tenant Django framework for building business apps"


install_requires = get_requirements("base")

setup(
    name="zango",
    version=PLATFORM_VERSION,
    license="Apache License 2.0",
    description="Zango: multi-tenant Django framework for building business apps",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author='Zelthy ("Healthlane Technologies")',
    author_email="maintainers@zelthy.com",
    url="https://github.com/Healthlane-Technologies/Zango",
    project_urls={
        "Bug Reports": "https://github.com/Healthlane-Technologies/Zango/issues",
        "Source": "https://github.com/Healthlane-Technologies/Zango",
        "Documentation": "https://github.com/Healthlane-Technologies/Zango#readme",
    },
    package_dir={"": "src"},
    packages=find_packages("src"),
    package_data={
        "zango": [
            "cli/project_template/**/*",
            "assets/**/*",
            "**/templates/**/*",
            "**/workspace_folder_template/**/*",
        ],
    },
    include_package_data=True,
    install_requires=install_requires,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="django multi-tenant framework business apps",
    entry_points={
        "console_scripts": [
            "zango=zango.cli:cli",
        ],
    },
)
