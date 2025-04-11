"""Configuration settings for the Digitized Journal application."""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = DATA_DIR / "images"
EXPORTS_DIR = DATA_DIR / "exports"

# Ensure directories exist
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)

# Database settings
DATABASE_URI = f"sqlite:///{DATA_DIR / 'journal.db'}"

# OCR settings
OCR_LANGUAGE = "eng"  # Language for Tesseract
OCR_CONFIG = "--psm 6"  # Page segmentation mode: Assume single uniform block of text

# Image preprocessing settings
IMAGE_RESIZE_WIDTH = 1800  # Width to resize images (maintain aspect ratio)
THRESHOLD_MIN = 150  # Minimum threshold value for binary conversion

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = DATA_DIR / "journal.log"