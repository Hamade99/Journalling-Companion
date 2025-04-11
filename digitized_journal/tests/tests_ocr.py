"""Test cases for the OCR module."""

import os
import unittest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from digitized_journal.ocr.preprocessor import ImagePreprocessor
from digitized_journal.ocr.ocr_engine import OCREngine

class TestImagePreprocessor(unittest.TestCase):
    """Test the image preprocessor functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.test_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Clean up test environment."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)
        
    @patch('cv2.imread')
    @patch('cv2.cvtColor')
    @patch('cv2.resize')
    @patch('cv2.adaptiveThreshold')
    @patch('cv2.fastNlMeansDenoising')
    @patch('PIL.Image.fromarray')
    def test_preprocess(self, mock_fromarray, mock_denoise, mock_threshold, 
                       mock_resize, mock_cvtcolor, mock_imread):
        """Test image preprocessing pipeline."""
        # Mock the CV2 functions
        mock_imread.return_value = MagicMock()
        mock_cvtcolor.return_value = MagicMock()
        mock_resize.return_value = MagicMock()
        mock_denoise.return_value = MagicMock()
        mock_threshold.return_value = MagicMock()
        mock_fromarray.return_value = MagicMock()
        
        # Create test image file
        test_image = self.test_dir / "test_image.jpg"
        with open(test_image, 'w') as f:
            f.write("dummy image content")
            
        # Process the image
        preprocessor = ImagePreprocessor()
        result = preprocessor.preprocess(test_image)
        
        # Check that functions were called
        mock_imread.assert_called_once_with(str(test_image))
        mock_cvtcolor.assert_called_once()
        mock_resize.assert_called_once()
        mock_denoise.assert_called_once()
        mock_threshold.assert_called_once()
        mock_fromarray.assert_called_once()
        
        # Check result
        self.assertEqual(result, mock_fromarray.return_value)
        
    def test_invalid_image(self):
        """Test handling of invalid image file."""
        # Create non-image file
        test_file = self.test_dir / "not_an_image.txt"
        with open(test_file, 'w') as f:
            f.write("This is not an image")
            
        # Attempt to preprocess
        preprocessor = ImagePreprocessor()
        with self.assertRaises(ValueError):
            preprocessor.preprocess(test_file)
            
class TestOCREngine(unittest.TestCase):
    """Test the OCR engine functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.test_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Clean up test environment."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)
        
    @patch('pytesseract.image_to_string')
    def test_process_image(self, mock_image_to_string):
        """Test basic OCR processing."""
        # Mock the tesseract function
        
        mock_image_to_string.return_value = "Test OCR output"
        
        # Create a mock PIL Image
        mock_image = MagicMock()
        
        # Mock the preprocessor
        mock_preprocessor = MagicMock()
        mock_preprocessor.preprocess.return_value = mock_image
        
        # Create test image file
        test_image = self.test_dir / "test_image.jpg"
        with open(test_image, 'w') as f:
            f.write("dummy image content")
            
        # Process the image
        engine = OCREngine()
        engine.preprocessor = mock_preprocessor
        
        result = engine.process_image(test_image)
        
        # Check preprocessing and OCR were called
        mock_preprocessor.preprocess.assert_called_once_with(test_image)
        mock_image_to_string.assert_called_once()
        
        # Check result
        self.assertEqual(result, "Test OCR output")
        
    def test_cleanup_text(self):
        """Test text cleanup functionality."""
        engine = OCREngine()
        
        # Test basic cleanup
        raw_text = "This  has  too   many    spaces\n\n\n\nAnd too many\nline breaks"
        expected = "This has too many spaces\n\nAnd too many line breaks"
        self.assertEqual(engine.cleanup_text(raw_text), expected)
        
        # Test OCR error corrections
        ocr_errors = "The |etter I and number 1 look sim|lar."
        expected = "The Ietter I and number 1 look simIlar."
        self.assertEqual(engine.cleanup_text(ocr_errors), expected)
        
        # Test punctuation spacing
        punctuation = "Word , another word . And more !"
        expected = "Word, another word. And more!"
        self.assertEqual(engine.cleanup_text(punctuation), expected)
        
        # Test apostrophes
        apostrophes = "It ' s not working"
        expected = "It's not working"
        self.assertEqual(engine.cleanup_text(apostrophes), expected)

if __name__ == '__main__':
    unittest.main()