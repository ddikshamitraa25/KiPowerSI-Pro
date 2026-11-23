from setuptools import setup, find_packages

setup(
    name="kipowersi",
    version="1.0.0",
    description="KiPowerSI Pro: Intelligent Power Distribution Network (PDN), IR-Drop & Thermal Parasitics Analyzer for KiCad 9",
    author="Anurag Thakur",
    author_email="contact-esim@fossee.in",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.20.0",
        "scipy>=1.7.0",
        "matplotlib>=3.4.0",
    ],
    extras_require={
        "test": ["pytest>=6.2.0"],
    },
    entry_points={
        "console_scripts": [
            "kipowersi=kipowersi.plugin:main_cli",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Manufacturing",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
)
