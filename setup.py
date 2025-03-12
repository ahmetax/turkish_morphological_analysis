#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="turkce-morfologik-analiz",
    version="0.1.0",
    author="Türkçe NLP",
    author_email="info@example.com",
    description="Öğrenebilen Türkçe Morfolojik Analiz Aracı",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kullanici/turkce-morfologik-analiz",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Natural Language :: Turkish",
    ],
    python_requires=">=3.6",
    install_requires=[
        "jpype1>=1.3.0",
        "configparser>=5.0.0",
        "matplotlib>=3.4.0",
    ],
    entry_points={
        "console_scripts": [
            "turkce-morfologik-analiz=turkce_morfologik_analiz:main",
            "turkce-rapor=rapor_araci:main",
            "turkce-coklu-islem=coklu_islem:main",
        ],
    },
)
