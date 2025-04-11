"""SQLAlchemy models for the journal application."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from typing import List, Optional

Base = declarative_base()

# Association table for Entry-Tag many-to-many relationship
entry_tag_association = Table(
    'entry_tag',
    Base.metadata,
    Column('entry_id', Integer, ForeignKey('entries.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)


class Entry(Base):
    """Journal entry model that can contain multiple pages."""
    __tablename__ = 'entries'

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=True)
    date = Column(DateTime, default=datetime.now)
    mood = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    pages = relationship('Page', back_populates='entry', order_by='Page.page_number', 
                         cascade="all, delete-orphan")
    tags = relationship('Tag', secondary=entry_tag_association, back_populates='entries')

    def __repr__(self):
        return f"<Entry(id={self.id}, title='{self.title}', date='{self.date.strftime('%Y-%m-%d')}')>"


class Page(Base):
    """A single page of a journal entry with image and OCR text."""
    __tablename__ = 'pages'

    id = Column(Integer, primary_key=True)
    entry_id = Column(Integer, ForeignKey('entries.id'), nullable=False)
    page_number = Column(Integer, nullable=False)
    image_path = Column(String(500), nullable=False)
    text_content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    entry = relationship('Entry', back_populates='pages')

    def __repr__(self):
        return f"<Page(id={self.id}, entry_id={self.entry_id}, page_number={self.page_number})>"


class Tag(Base):
    """Tags for journal entries."""
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    # Relationships
    entries = relationship('Entry', secondary=entry_tag_association, back_populates='tags')

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"