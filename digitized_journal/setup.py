"""Setup script for the Digital Journal application."""

from setuptools import setup, find_packages

setup(
    name="digitized_journal",
    version="0.1.0",
    description="A journal application with OCR for handwritten notes",
    author="Ahmad M",
    author_email="hellehamade@gmail.com",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "pytesseract>=0.3.9",
        "opencv-python>=4.5.5",
        "sqlalchemy>=1.4.0",
        "pillow>=9.0.0",
        "markdown>=3.3.0",
        "reportlab>=3.6.0",
    ],
    extras_require={
        "web": ["streamlit>=1.10.0"],
        "dev": ["pytest>=7.0.0", "black>=22.0.0", "flake8>=4.0.0"],
    },
    entry_points={
        "console_scripts": [
            "journal=digitized_journal.main:main",
        ],
    },
)