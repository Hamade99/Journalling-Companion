"""Utility functions for file operations."""

import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
import logging
from typing import List, Optional, Tuple, Union
from PIL import Image

logger = logging.getLogger(__name__)

def create_unique_filename(original_path: Union[str, Path], prefix: Optional[str] = None) -> str:
    """
    Create a unique filename based on original file.
    
    Args:
        original_path: Original file path
        prefix: Optional prefix to add
        
    Returns:
        Unique filename with extension
    """
    path = Path(original_path)
    base = prefix + "_" if prefix else ""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    
    return f"{base}{timestamp}_{unique_id}{path.suffix}"

def verify_image_file(image_path: Union[str, Path]) -> bool:
    """
    Verify that a file is a valid image.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        True if valid image, False otherwise
    """
    try:
        with Image.open(image_path) as img:
            img.verify()  # Verify image file
        return True
    except Exception as e:
        logger.warning(f"Invalid image file: {image_path}, error: {str(e)}")
        return False

def get_image_dimensions(image_path: Union[str, Path]) -> Tuple[int, int]:
    """
    Get image dimensions.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Tuple of (width, height)
    """
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception as e:
        logger.error(f"Error getting image dimensions: {str(e)}")
        raise

def save_uploaded_file(uploaded_file: bytes, target_dir: Union[str, Path], 
                      filename: Optional[str] = None) -> Path:
    """
    Save an uploaded file to the target directory.
    
    Args:
        uploaded_file: Uploaded file data as bytes
        target_dir: Directory to save the file
        filename: Optional custom filename (generated if None)
        
    Returns:
        Path to the saved file
    """
    target_dir = Path(target_dir)
    os.makedirs(target_dir, exist_ok=True)
    
    if not filename:
        filename = create_unique_filename("temp.jpg", "upload")
        
    file_path = target_dir / filename
    
    try:
        with open(file_path, 'wb') as f:
            f.write(uploaded_file)
        
        # Verify it's a valid image after saving
        if not verify_image_file(file_path):
            os.remove(file_path)
            raise ValueError("Invalid image file")
            
        return file_path
        
    except Exception as e:
        logger.error(f"Error saving uploaded file: {str(e)}")
        # Clean up in case of error
        if file_path.exists():
            os.remove(file_path)
        raise

def list_image_files(directory: Union[str, Path]) -> List[Path]:
    """
    List all image files in a directory.
    
    Args:
        directory: Directory to scan
        
    Returns:
        List of paths to image files
    """
    directory = Path(directory)
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
    
    image_files = []
    
    if not directory.exists():
        return []
        
    for item in directory.iterdir():
        if item.is_file() and item.suffix.lower() in image_extensions:
            if verify_image_file(item):
                image_files.append(item)
                
    return image_files

def copy_file_to_dir(file_path: Union[str, Path], target_dir: Union[str, Path], 
                   new_filename: Optional[str] = None) -> Path:
    """
    Copy a file to a target directory.
    
    Args:
        file_path: Source file path
        target_dir: Target directory
        new_filename: Optional new filename
        
    Returns:
        Path to the copied file
    """
    file_path = Path(file_path)
    target_dir = Path(target_dir)
    
    os.makedirs(target_dir, exist_ok=True)
    
    if not new_filename:
        new_filename = file_path.name
        
    target_path = target_dir / new_filename
    
    try:
        return Path(shutil.copy2(file_path, target_path))
    except Exception as e:
        logger.error(f"Error copying file: {str(e)}")
        raise