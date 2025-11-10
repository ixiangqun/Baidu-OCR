#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR-Baidu-Processor 安装配置
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README文件
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# 读取版本信息
about = {}
exec((this_directory / "src" / "__version__.py").read_text(encoding='utf-8'), about)

setup(
    name="ocr-baidu-processor",
    version=about["__version__"],
    author=about["__author__"],
    author_email=about["__email__"],
    description=about["__description__"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ocr-baidu-processor",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: General",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        "Pillow>=8.0.0",
        "tqdm>=4.60.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.10.0",
            "flake8>=3.8.0",
            "black>=21.0.0",
            "isort>=5.0.0",
        ],
        "enhanced": [
            "opencv-python>=4.5.0",
            "numpy>=1.19.0",
            "pandas>=1.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ocr-baidu-processor=main:main",
            "ocr-baidu=main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)