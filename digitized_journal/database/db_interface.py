"""Database interface for the journal application."""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy import create_engine, func, or_
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError

from ..database.models import Base, Entry, Page, Tag
from ..config import DATABASE_URI

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Interface for database operations."""
    
    def __init__(self, db_uri: str = DATABASE_URI):
        """Initialize database connection."""
        self.engine = create_engine(db_uri)
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        
    def initialize_database(self) -> None:
        """Create database tables if they don't exist."""
        Base.metadata.create_all(self.engine)
        logger.info("Database initialized successfully")
        
    def get_session(self):
        """Get a new database session."""
        return self.Session()
        
    def close_sessions(self) -> None:
        """Close all sessions."""
        self.Session.remove()
        
    # Entry CRUD operations
    def create_entry(self, 
                    title: Optional[str] = None, 
                    date: Optional[datetime] = None, 
                    mood: Optional[str] = None, 
                    tags: Optional[List[str]] = None) -> int:
        """Create a new journal entry."""
        session = self.get_session()
        try:
            entry = Entry(title=title, date=date or datetime.now(), mood=mood)
            
            # Handle tags
            if tags:
                for tag_name in tags:
                    tag = session.query(Tag).filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        session.add(tag)
                    entry.tags.append(tag)
                    
            session.add(entry)
            session.commit()
            return entry.id
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error creating entry: {str(e)}")
            raise
        finally:
            session.close()
            
    def get_entry(self, entry_id: int) -> Optional[Entry]:
        """Get an entry by ID."""
        session = self.get_session()
        try:
            entry = session.query(Entry).filter_by(id=entry_id).first()
            return entry
        finally:
            session.close()
            
    def get_all_entries(self) -> List[Entry]:
        """Get all journal entries ordered by date."""
        session = self.get_session()
        try:
            entries = session.query(Entry).order_by(Entry.date.desc()).all()
            return entries
        finally:
            session.close()
            
    def update_entry(self, 
                    entry_id: int, 
                    title: Optional[str] = None, 
                    date: Optional[datetime] = None, 
                    mood: Optional[str] = None, 
                    tags: Optional[List[str]] = None) -> bool:
        """Update an existing entry."""
        session = self.get_session()
        try:
            entry = session.query(Entry).filter_by(id=entry_id).first()
            if not entry:
                return False
                
            if title is not None:
                entry.title = title
            if date is not None:
                entry.date = date
            if mood is not None:
                entry.mood = mood
                
            # Update tags if provided
            if tags is not None:
                # Clear existing tags
                entry.tags.clear()
                
                # Add new tags
                for tag_name in tags:
                    tag = session.query(Tag).filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        session.add(tag)
                    entry.tags.append(tag)
                    
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error updating entry: {str(e)}")
            raise
        finally:
            session.close()
            
    def delete_entry(self, entry_id: int) -> bool:
        """Delete an entry and all its pages."""
        session = self.get_session()
        try:
            entry = session.query(Entry).filter_by(id=entry_id).first()
            if not entry:
                return False
                
            session.delete(entry)
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error deleting entry: {str(e)}")
            raise
        finally:
            session.close()
            
    # Page CRUD operations
    def add_page(self, 
                entry_id: int, 
                page_number: int, 
                image_path: str, 
                text_content: Optional[str] = None) -> int:
        """Add a page to an entry."""
        session = self.get_session()
        try:
            page = Page(
                entry_id=entry_id,
                page_number=page_number,
                image_path=image_path,
                text_content=text_content
            )
            session.add(page)
            session.commit()
            return page.id
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error adding page: {str(e)}")
            raise
        finally:
            session.close()
            
    def get_page(self, page_id: int) -> Optional[Page]:
        """Get a page by ID."""
        session = self.get_session()
        try:
            page = session.query(Page).filter_by(id=page_id).first()
            return page
        finally:
            session.close()
            
    def update_page_text(self, page_id: int, text_content: str) -> bool:
        """Update the text content of a page."""
        session = self.get_session()
        try:
            page = session.query(Page).filter_by(id=page_id).first()
            if not page:
                return False
                
            page.text_content = text_content
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error updating page text: {str(e)}")
            raise
        finally:
            session.close()
            
    def delete_page(self, page_id: int) -> bool:
        """Delete a page."""
        session = self.get_session()
        try:
            page = session.query(Page).filter_by(id=page_id).first()
            if not page:
                return False
                
            session.delete(page)
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error deleting page: {str(e)}")
            raise
        finally:
            session.close()
    
    # Tag operations
    def get_all_tags(self) -> List[Tag]:
        """Get all tags."""
        session = self.get_session()
        try:
            tags = session.query(Tag).order_by(Tag.name).all()
            return tags
        finally:
            session.close()
    
    # Search operations
    def search_entries(self, query: Optional[str] = None, tag: Optional[str] = None) -> List[Entry]:
        """
        Search for entries containing the query text and/or tag.
        
        Args:
            query: Text to search in content
            tag: Tag name to filter by
            
        Returns:
            List of matching entries
        """
        session = self.get_session()
        try:
            # Start with base query
            entries_query = session.query(Entry).distinct()
            
            # Filter by text content if query provided
            if query:
                entries_query = entries_query.join(Entry.pages).filter(
                    # Search in title or text content
                    or_(
                        Entry.title.ilike(f'%{query}%'),
                        Page.text_content.ilike(f'%{query}%')
                    )
                )
                
            # Filter by tag if provided
            if tag:
                entries_query = entries_query.join(Entry.tags).filter(
                    Tag.name == tag
                )
                
            # Order by date (newest first)
            entries_query = entries_query.order_by(Entry.date.desc())
                
            return entries_query.all()
        finally:
            session.close()