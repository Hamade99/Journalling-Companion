"""Business logic for managing journal entries and pages."""

import shutil
import uuid
from datetime import datetime
from pathlib import Path
import logging
from typing import List, Optional, Dict, Any, Union, Tuple

from ..database.db_interface import DatabaseManager
from ..database.models import Entry, Page
from ..ocr.ocr_engine import OCREngine
from ..config import IMAGES_DIR

logger = logging.getLogger(__name__)

class EntryManager:
    """Manages journal entries and their pages."""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None, ocr_engine: Optional[OCREngine] = None):
        """
        Initialize the entry manager.
        
        Args:
            db_manager: Database manager instance or None to create new
            ocr_engine: OCR engine instance or None to create new
        """
        self.db_manager = db_manager or DatabaseManager()
        self.ocr_engine = ocr_engine or OCREngine()
        
    def create_entry(self, 
                    title: Optional[str] = None, 
                    date: Optional[datetime] = None, 
                    mood: Optional[str] = None, 
                    tags: Optional[List[str]] = None) -> int:
        """
        Create a new journal entry.
        
        Args:
            title: Optional title for the entry
            date: Optional date (defaults to current datetime)
            mood: Optional mood/emotion indicator
            tags: Optional list of tags
            
        Returns:
            ID of the created entry
        """
        if date is None:
            date = datetime.now()
            
        return self.db_manager.create_entry(
            title=title,
            date=date,
            mood=mood,
            tags=tags
        )
        
    def add_page_from_image(self, 
                           entry_id: int, 
                           image_path: Union[str, Path], 
                           page_number: Optional[int] = None, 
                           preprocess: bool = True) -> int:
        """
        Add a page to an entry from an image.
        
        Args:
            entry_id: ID of the entry
            image_path: Path to the image file
            page_number: Optional page number (auto-assigned if None)
            preprocess: Whether to preprocess the image before OCR
            
        Returns:
            ID of the created page
        """
        # Get entry
        entry = self.db_manager.get_entry(entry_id)
        if not entry:
            raise ValueError(f"Entry with ID {entry_id} not found")
            
        # Determine page number if not specified
        if page_number is None:
            existing_pages = len(entry.pages)
            page_number = existing_pages + 1
            
        # Create directory for entry if it doesn't exist
        entry_dir = IMAGES_DIR / str(entry_id)
        entry_dir.mkdir(exist_ok=True)
        
        # Copy image to storage
        image_filename = f"{uuid.uuid4()}{Path(image_path).suffix}"
        target_path = entry_dir / image_filename
        shutil.copy2(image_path, target_path)
        
        # Extract text via OCR
        try:
            ocr_result = self.ocr_engine.process_image_with_confidence(
                target_path, preprocess=preprocess
            )
            text_content = ocr_result['text']
            
            logger.info(f"OCR completed with confidence: {ocr_result['confidence']:.2f}%, "
                       f"word count: {ocr_result['word_count']}")
                       
        except Exception as e:
            logger.error(f"OCR failed for {image_path}: {str(e)}")
            text_content = ""  # Empty text if OCR fails
            
        # Save page to database
        return self.db_manager.add_page(
            entry_id=entry_id,
            page_number=page_number,
            image_path=str(target_path),
            text_content=text_content
        )
        
    def add_multiple_pages(self, 
                          entry_id: int, 
                          image_paths: List[Union[str, Path]], 
                          preprocess: bool = True) -> List[int]:
        """
        Add multiple pages to an entry from images.
        
        Args:
            entry_id: ID of the entry
            image_paths: List of paths to image files
            preprocess: Whether to preprocess images before OCR
            
        Returns:
            List of page IDs
        """
        # Get entry
        entry = self.db_manager.get_entry(entry_id)
        if not entry:
            raise ValueError(f"Entry with ID {entry_id} not found")
            
        # Process each image
        page_ids = []
        start_page_number = len(entry.pages) + 1
        
        for i, image_path in enumerate(image_paths):
            page_id = self.add_page_from_image(
                entry_id=entry_id,
                image_path=image_path,
                page_number=start_page_number + i,
                preprocess=preprocess
            )
            page_ids.append(page_id)
            
        return page_ids
        
    def update_page_text(self, page_id: int, text_content: str) -> bool:
        """
        Update the OCR text of a page manually.
        
        Args:
            page_id: ID of the page
            text_content: New text content
            
        Returns:
            Success status
        """
        return self.db_manager.update_page_text(page_id, text_content)
        
    def update_entry(self, 
                    entry_id: int, 
                    title: Optional[str] = None, 
                    date: Optional[datetime] = None, 
                    mood: Optional[str] = None, 
                    tags: Optional[List[str]] = None) -> bool:
        """
        Update entry metadata.
        
        Args:
            entry_id: ID of the entry
            title: New title (None to keep current)
            date: New date (None to keep current)
            mood: New mood (None to keep current)
            tags: New tags (None to keep current)
            
        Returns:
            Success status
        """
        return self.db_manager.update_entry(
            entry_id=entry_id,
            title=title,
            date=date,
            mood=mood,
            tags=tags
        )
        
    def get_entry_with_pages(self, entry_id: int) -> Optional[Entry]:
        """Get an entry with all its pages."""
        session = self.db_manager.get_session()
        try:
            entry = session.query(Entry).filter_by(id=entry_id).first()
            if entry:
                # Force loading pages while session is still open
                _ = list(entry.pages)
            return entry
        finally:
            session.close()
        
    def get_all_entries(self) -> List[Entry]:
        """
        Get all journal entries.
        
        Returns:
            List of Entry objects ordered by date (newest first)
        """
        return self.db_manager.get_all_entries()
        
    def search_entries(self, query: Optional[str] = None, tag: Optional[str] = None) -> List[Entry]:
        """
        Search for entries.
        
        Args:
            query: Text to search for (optional)
            tag: Tag to filter by (optional)
            
        Returns:
            List of matching Entry objects
        """
        return self.db_manager.search_entries(query, tag)
        
    def delete_entry(self, entry_id: int) -> bool:
        """
        Delete an entry and its pages.
        
        Args:
            entry_id: ID of the entry
            
        Returns:
            Success status
        """
        # Get entry to find its images
        entry = self.db_manager.get_entry(entry_id)
        if not entry:
            return False
            
        # Delete entry from database (cascades to pages)
        result = self.db_manager.delete_entry(entry_id)
        
        if result:
            # Delete entry directory with images
            entry_dir = IMAGES_DIR / str(entry_id)
            if entry_dir.exists():
                shutil.rmtree(entry_dir)
                
        return result
        
    def reprocess_page_ocr(self, page_id: int, preprocess: bool = True) -> Optional[str]:
        """
        Re-run OCR on an existing page.
        
        Args:
            page_id: ID of the page
            preprocess: Whether to preprocess the image
            
        Returns:
            New text content or None if failed
        """
        # Get the page
        page = self.db_manager.get_page(page_id)
        if not page:
            logger.error(f"Page with ID {page_id} not found")
            return None
            
        try:
            # Re-process the image
            text_content = self.ocr_engine.process_image(
                page.image_path, preprocess=preprocess
            )
            
            # Update the page text
            self.db_manager.update_page_text(page_id, text_content)
            
            return text_content
            
        except Exception as e:
            logger.error(f"Error reprocessing OCR for page {page_id}: {str(e)}")
            return None