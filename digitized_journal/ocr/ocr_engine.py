"""OCR engine for extracting text from images."""

import pytesseract
import re
import logging
from pathlib import Path
from PIL import Image
from typing import Union, Dict, Any, Optional

from ..config import OCR_LANGUAGE, OCR_CONFIG
from .preprocessor import ImagePreprocessor

logger = logging.getLogger(__name__)

class OCREngine:
    """Handles OCR processing using Tesseract."""
    
    def __init__(self, lang: str = OCR_LANGUAGE, config: str = OCR_CONFIG):
        """
        Initialize the OCR engine.
        
        Args:
            lang: Language for OCR (default: eng)
            config: Tesseract configuration string
        """
        self.lang = lang
        self.config = config
        self.preprocessor = ImagePreprocessor()
        
    def process_image(self, 
                      image_path: Union[str, Path], 
                      preprocess: bool = True, 
                      cleanup_text: bool = True) -> str:
        """
        Extract text from an image.
        
        Args:
            image_path: Path to the image file
            preprocess: Whether to preprocess the image
            cleanup_text: Whether to clean up the extracted text
            
        Returns:
            Extracted text
        """
        logger.info(f"Processing image for OCR: {image_path}")
        
        try:
            image_path = Path(image_path)
            
            # Preprocess image
            if preprocess:
                image = self.preprocessor.preprocess(image_path)
            else:
                image = Image.open(image_path)
                
            # Extract text
            pytesseract.pytesseract.tesseract_cmd = r'C:\Users\nxg11379\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
            text = pytesseract.image_to_string(image, lang=self.lang, config=self.config)
            
            # Clean up text
            if cleanup_text:
                text = self.cleanup_text(text)
                
            return text
            
        except Exception as e:
            logger.error(f"OCR processing failed: {str(e)}")
            raise
    
    def process_image_with_confidence(self, 
                                     image_path: Union[str, Path], 
                                     preprocess: bool = True) -> Dict[str, Any]:
        """
        Extract text with confidence scores from an image.
        
        Args:
            image_path: Path to the image file
            preprocess: Whether to preprocess the image
            
        Returns:
            Dictionary with text and confidence metrics
        """
        try:
            image_path = Path(image_path)
            
            # Preprocess image
            if preprocess:
                image = self.preprocessor.preprocess(image_path)
            else:
                image = Image.open(image_path)
                
            # Get confidence data
            data = pytesseract.image_to_data(image, lang=self.lang, config=self.config, 
                                           output_type=pytesseract.Output.DICT)
            
            # Extract text and calculate average confidence
            text_parts = []
            confidence_values = []
            
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 0:  # Skip entries with -1 confidence
                    text_parts.append(data['text'][i])
                    confidence_values.append(int(data['conf'][i]))
            
            full_text = " ".join(text_parts)
            avg_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0
            
            if full_text:
                full_text = self.cleanup_text(full_text)
                
            return {
                'text': full_text,
                'confidence': avg_confidence,
                'word_count': len(text_parts)
            }
            
        except Exception as e:
            logger.error(f"OCR processing with confidence failed: {str(e)}")
            raise
            
    def cleanup_text(self, text: str) -> str:
        """
        Clean up OCR text output.
        
        Args:
            text: Raw OCR text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
            
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix line breaks (keep paragraph structure)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Common OCR error corrections
        replacements = {
            '|': 'I',             # Vertical bar to letter I
            '{': '(',             # Common bracket confusions
            '}': ')',
            '0': 'O',             # Common number/letter confusions in context
            '1': 'I',
            '5': 'S',
        }
        
        # Only replace when it makes sense (surrounded by letters)
        for err, fix in replacements.items():
            # Look for the error character between letters
            text = re.sub(f'(?<=[a-zA-Z]){re.escape(err)}(?=[a-zA-Z])', fix, text)
        
        # Fix spacing around punctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        
        # Fix common spacing issues
        text = re.sub(r'(\w)\s+(\')(\w)', r'\1\2\3', text)  # Fix a ' s -> a's
        
        return text.strip()