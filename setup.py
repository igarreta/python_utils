"""
Setup script for python_utils package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="python-utils-igarreta",
    version="0.1.0",
    author="igarreta",
    author_email="",
    description="Comprehensive Python utilities for backup monitoring and system administration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/igarreta/python_utils",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: System :: Archiving :: Backup",
        "Topic :: System :: Systems Administration",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications :: Email",
        "Topic :: System :: Logging",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    keywords="backup monitoring utilities email notifications pushover logging filesystem",
    project_urls={
        "Bug Reports": "https://github.com/igarreta/python_utils/issues",
        "Source": "https://github.com/igarreta/python_utils",
        "Documentation": "https://github.com/igarreta/python_utils#readme",
    },
)