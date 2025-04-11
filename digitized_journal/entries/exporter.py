"""Export journal entries to various formats."""

import os
from pathlib import Path
import logging
from datetime import datetime
from typing import Optional, List, Union, Dict, Any
import markdown
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from PIL import Image

from ..database.models import Entry, Page
from ..config import EXPORTS_DIR

logger = logging.getLogger(__name__)

class EntryExporter:
    """Exports journal entries to various formats."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the exporter.
        
        Args:
            output_dir: Directory for export outputs (default: EXPORTS_DIR from config)
        """
        self.output_dir = output_dir or EXPORTS_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        
    def to_markdown(self, entry: Entry, output_path: Optional[Path] = None) -> Path:
        """
        Export an entry to Markdown format.
        
        Args:
            entry: Entry object to export
            output_path: Optional custom output path
            
        Returns:
            Path to the created Markdown file
        """
        if output_path is None:
            date_str = entry.date.strftime('%Y-%m-%d')
            title_slug = entry.title.lower().replace(' ', '-') if entry.title else 'untitled'
            filename = f"{date_str}_{title_slug}.md"
            output_path = self.output_dir / filename
            
        with open(output_path, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"# {entry.title or 'Untitled Entry'}\n\n")
            
            # Write metadata
            f.write(f"Date: {entry.date.strftime('%Y-%m-%d %H:%M')}\n")
            
            if entry.mood:
                f.write(f"Mood: {entry.mood}\n")
                
            if entry.tags:
                tag_list = ', '.join([tag.name for tag in entry.tags])
                f.write(f"Tags: {tag_list}\n")
                
            f.write("\n---\n\n")
            
            # Write pages
            for page in entry.pages:
                f.write(f"## Page {page.page_number}\n\n")
                
                # Add image reference
                image_path = Path(page.image_path)
                f.write(f"![Page {page.page_number} Image]({image_path})\n\n")
                
                # Add text content
                if page.text_content:
                    f.write(page.text_content)
                    
                f.write("\n\n---\n\n")
                
        logger.info(f"Markdown export completed: {output_path}")
        return output_path
        
    def to_pdf(self, entry: Entry, output_path: Optional[Path] = None, 
              include_images: bool = True, max_image_width: int = 5) -> Path:
        """
        Export an entry to PDF format.
        
        Args:
            entry: Entry object to export
            output_path: Optional custom output path
            include_images: Whether to include page images
            max_image_width: Maximum width of images in inches
            
        Returns:
            Path to the created PDF file
        """
        if output_path is None:
            date_str = entry.date.strftime('%Y-%m-%d')
            title_slug = entry.title.lower().replace(' ', '-') if entry.title else 'untitled'
            filename = f"{date_str}_{title_slug}.pdf"
            output_path = self.output_dir / filename
            
        # Set up PDF styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            alignment=TA_CENTER,
            spaceAfter=12
        )
        heading_style = styles['Heading2']
        normal_style = styles['Normal']
        metadata_style = ParagraphStyle(
            'MetadataStyle',
            parent=styles['Italic'],
            alignment=TA_LEFT,
            fontSize=9,
            spaceAfter=6
        )
        
        # Create document
        doc = SimpleDocTemplate(str(output_path), pagesize=letter,
                             rightMargin=72, leftMargin=72,
                             topMargin=72, bottomMargin=72)
                             
        # Prepare content elements
        elements = []
        
        # Title
        elements.append(Paragraph(entry.title or "Untitled Entry", title_style))
        elements.append(Spacer(1, 12))
        
        # Metadata
        metadata = []
        metadata.append(f"Date: {entry.date.strftime('%Y-%m-%d %H:%M')}")
        
        if entry.mood:
            metadata.append(f"Mood: {entry.mood}")
            
        if entry.tags:
            tag_list = ', '.join([tag.name for tag in entry.tags])
            metadata.append(f"Tags: {tag_list}")
            
        for meta in metadata:
            elements.append(Paragraph(meta, metadata_style))
            
        elements.append(Spacer(1, 24))
        
        # Pages content
        for page in entry.pages:
            # Page heading
            elements.append(Paragraph(f"Page {page.page_number}", heading_style))
            elements.append(Spacer(1, 12))
            
            # Image
            if include_images and os.path.exists(page.image_path):
                try:
                    # Calculate image dimensions
                    img = Image.open(page.image_path)
                    width, height = img.size
                    aspect = height / width
                    
                    img_width = min(max_image_width * inch, 6 * inch)  # Limit width
                    img_height = img_width * aspect
                    
                    # Add image
                    elements.append(RLImage(page.image_path, width=img_width, height=img_height))
                    elements.append(Spacer(1, 12))
                except Exception as e:
                    logger.error(f"Error adding image to PDF: {str(e)}")
                    
            # Text content
            if page.text_content:
                paragraphs = page.text_content.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        elements.append(Paragraph(para.replace('\n', '<br/>'), normal_style))
                        elements.append(Spacer(1, 6))
                        
            # Page separator
            elements.append(Spacer(1, 20))
            if page != entry.pages[-1]:  # If not the last page
                elements.append(PageBreak())
                
        # Build PDF
        doc.build(elements)
        
        logger.info(f"PDF export completed: {output_path}")
        return output_path
        
    def _format_metadata(self, entry: Entry) -> str:
        """Format entry metadata as text."""
        meta = []
        
        if entry.title:
            meta.append(f"Title: {entry.title}")
            
        meta.append(f"Date: {entry.date.strftime('%Y-%m-%d %H:%M')}")
        
        if entry.mood:
            meta.append(f"Mood: {entry.mood}")
            
        if entry.tags:
            tag_list = ', '.join([tag.name for tag in entry.tags])
            meta.append(f"Tags: {tag_list}")
            
        return '\n'.join(meta)