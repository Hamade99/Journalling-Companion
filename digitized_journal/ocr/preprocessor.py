"""Image preprocessing for better OCR results."""

import cv2
import numpy as np
from pathlib import Path
from PIL import Image
import logging
from typing import Tuple, Optional, Union

from ..config import IMAGE_RESIZE_WIDTH, THRESHOLD_MIN

logger = logging.getLogger(__name__)

class ImagePreprocessor:
    """Handles preprocessing of images for better OCR results."""
    
    @staticmethod
    def preprocess(image_path: Union[str, Path], 
                  resize: Optional[Tuple[int, int]] = None, 
                  denoise: bool = True, 
                  threshold: bool = True,
                  deskew: bool = True) -> Image.Image:
        """
        Preprocess an image for OCR.
        
        Args:
            image_path: Path to the image file
            resize: Optional tuple (width, height) for resizing
            denoise: Apply noise reduction
            threshold: Apply adaptive thresholding
            deskew: Correct image skew
            
        Returns:
            PIL Image ready for OCR
        """
        logger.info(f"Preprocessing image: {image_path}")
        
        # Read image
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Failed to load image: {image_path}")
            
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Resize if needed
        if resize:
            width, height = resize
            gray = cv2.resize(gray, (width, height))
        elif IMAGE_RESIZE_WIDTH > 0:
            # Resize to fixed width while maintaining aspect ratio
            height, width = gray.shape[:2]
            ratio = IMAGE_RESIZE_WIDTH / width
            new_height = int(height * ratio)
            gray = cv2.resize(gray, (IMAGE_RESIZE_WIDTH, new_height))
        
        # Deskew if requested
        if deskew:
            gray = ImagePreprocessor._deskew(gray)
        
        # Apply denoising
        if denoise:
            gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            
        # Apply thresholding
        if threshold:
            gray = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
        # Convert to PIL Image for Tesseract
        pil_img = Image.fromarray(gray)
        
        return pil_img
        
    @staticmethod
    def _deskew(image: np.ndarray) -> np.ndarray:
        """
        Deskew an image to straighten text.
        
        Args:
            image: Grayscale image as numpy array
            
        Returns:
            Deskewed image
        """
        # Threshold to find all text contours
        thresh = cv2.threshold(image, THRESHOLD_MIN, 255, 
                             cv2.THRESH_BINARY_INV)[1] 
        
        # Find contours and calculate bounding box
        coords = np.column_stack(np.where(thresh > 0))
        
        # If no valid coordinates, return original image
        if len(coords) <= 10:
            return image
            
        angle = cv2.minAreaRect(coords)[-1]
        
        # Adjust angle
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
            
        # Skip correction if angle is very small
        if abs(angle) < 0.5:
            return image
            
        # Rotate to deskew
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        deskewed = cv2.warpAffine(
            image, M, (w, h), flags=cv2.INTER_CUBIC, 
            borderMode=cv2.BORDER_REPLICATE
        )
        
        return deskewed
        
    @staticmethod
    def enhance_contrast(image: np.ndarray) -> np.ndarray:
        """
        Enhance the contrast of an image.
        
        Args:
            image: Grayscale image
            
        Returns:
            Contrast-enhanced image
        """
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(image)
        
        return enhanced