"""Streamlit web interface for the journal application."""

import os
import streamlit as st
import tempfile
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
import pandas as pd
import io
from PIL import Image
import logging

from digitized_journal.database.db_interface import DatabaseManager
from digitized_journal.entries.entry_manager import EntryManager
from digitized_journal.entries.exporter import EntryExporter
from digitized_journal.utils.file_utils import save_uploaded_file, verify_image_file
from digitized_journal.config import DATA_DIR, IMAGES_DIR

logger = logging.getLogger(__name__)

class StreamlitApp:
    """Streamlit web interface for the journal application."""
    
    def __init__(self):
        """Initialize the app components."""
        # Set up page config
        st.set_page_config(
            page_title="Digital Journal",
            page_icon="📔",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Initialize components
        self.db_manager = DatabaseManager()
        self.db_manager.initialize_database()
        self.entry_manager = EntryManager(db_manager=self.db_manager)
        self.exporter = EntryExporter()
        
        # Set up session state
        if 'current_view' not in st.session_state:
            st.session_state.current_view = 'list'
        if 'current_entry_id' not in st.session_state:
            st.session_state.current_entry_id = None
        if 'search_query' not in st.session_state:
            st.session_state.search_query = ""
        if 'search_tag' not in st.session_state:
            st.session_state.search_tag = ""
            
    def run(self):
        """Run the Streamlit app."""
        # Display header
        st.title("Digital Journal")
        
        # Sidebar navigation
        self._show_sidebar()
        
        # Main content based on current view
        if st.session_state.current_view == 'list':
            self._show_entries_list()
        elif st.session_state.current_view == 'view':
            self._show_entry_detail()
        elif st.session_state.current_view == 'new':
            self._show_new_entry_form()
        elif st.session_state.current_view == 'edit':
            self._show_edit_entry_form()
        elif st.session_state.current_view == 'search':
            self._show_search_view()
        elif st.session_state.current_view == 'stats':
            self._show_stats_view()
            
    def _show_sidebar(self):
        """Display the sidebar navigation."""
        with st.sidebar:
            st.header("Navigation")
            
            # Main navigation buttons
            if st.button("📝 New Entry"):
                st.session_state.current_view = 'new'
                st.rerun()
                
            if st.button("📚 All Entries"):
                st.session_state.current_view = 'list'
                st.rerun()
                
            if st.button("🔍 Search"):
                st.session_state.current_view = 'search'
                st.rerun()
                
            if st.button("📊 Statistics"):
                st.session_state.current_view = 'stats'
                st.rerun()
                
            # Tags for filtering
            st.subheader("Filter by Tag")
            tags = self.db_manager.get_all_tags()
            
            for tag in tags:
                if st.button(f"#{tag.name}", key=f"tag_{tag.id}"):
                    st.session_state.search_tag = tag.name
                    st.session_state.current_view = 'search'
                    st.rerun()
                    
    def _show_entries_list(self):
        """Display a list of all entries."""
        st.header("Journal Entries")
        
        entries = self.entry_manager.get_all_entries()
        
        if not entries:
            st.info("No entries found. Create your first entry!")
            return
            
        # Create a column display
        for i in range(0, len(entries), 3):
            cols = st.columns(3)
            
            for j in range(3):
                idx = i + j
                if idx < len(entries):
                    entry = entries[idx]
                    with cols[j]:
                        self._display_entry_card(entry)
                        
    def _display_entry_card(self, entry):
        """Display an entry card."""
        # Prepare data for display
        title = entry.title or "Untitled Entry"
        date_str = entry.date.strftime("%Y-%m-%d")
        tags = ", ".join([tag.name for tag in entry.tags]) if entry.tags else "No tags"
        page_count = len(entry.pages)
        mood = entry.mood or ""
        
        # Create card with border
        with st.container(border=True):
            # Title and date
            st.subheader(title)
            st.caption(f"Date: {date_str}")
            
            # Mood emoji if present
            if mood:
                st.write(f"Mood: {mood}")
                
            # Display first page preview if available
            if page_count > 0 and entry.pages[0].image_path:
                try:
                    img_path = Path(entry.pages[0].image_path)
                    if img_path.exists():
                        image = Image.open(img_path)
                        st.image(image, width=200)
                except Exception as e:
                    st.error(f"Error displaying image: {str(e)}")
                    
            # Tags and page count
            st.write(f"Pages: {page_count} | Tags: {tags}")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("View", key=f"view_{entry.id}"):
                    st.session_state.current_entry_id = entry.id
                    st.session_state.current_view = 'view'
                    st.rerun()
                    
            with col2:
                if st.button("Edit", key=f"edit_{entry.id}"):
                    st.session_state.current_entry_id = entry.id
                    st.session_state.current_view = 'edit'
                    st.rerun()
                    
            with col3:
                if st.button("Delete", key=f"delete_{entry.id}"):
                    if self._delete_entry(entry.id):
                        st.rerun()
                        
    def _show_entry_detail(self):
        """Display the details of a single entry."""
        if not st.session_state.current_entry_id:
            st.error("No entry selected")
            return
            
        entry = self.entry_manager.get_entry_with_pages(st.session_state.current_entry_id)
        
        if not entry:
            st.error("Entry not found")
            st.session_state.current_view = 'list'
            st.rerun()
            return
            
        # Entry header
        st.header(entry.title or "Untitled Entry")
        st.subheader(f"Date: {entry.date.strftime('%Y-%m-%d')}")
        
        # Metadata
        col1, col2 = st.columns(2)
        
        with col1:
            if entry.mood:
                st.write(f"Mood: {entry.mood}")
                
        with col2:
            if entry.tags:
                tags_str = ", ".join([tag.name for tag in entry.tags])
                st.write(f"Tags: {tags_str}")
                
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Edit Entry"):
                st.session_state.current_view = 'edit'
                st.rerun()
                
        with col2:
            if st.button("Export as Markdown"):
                self._export_entry(entry, 'md')
                
        with col3:
            if st.button("Export as PDF"):
                self._export_entry(entry, 'pdf')
                
        # Pages content with tabs
        if entry.pages:
            st.subheader("Pages")
            
            # Create tabs for each page
            tabs = st.tabs([f"Page {page.page_number}" for page in entry.pages])
            
            for i, page in enumerate(entry.pages):
                with tabs[i]:
                    self._display_page_detail(page, entry.id)
        else:
            st.info("This entry has no pages yet.")
            
        # Add page option
        st.subheader("Add New Page")
        self._show_add_page_form(entry.id)
        
    def _display_page_detail(self, page, entry_id):
        """Display the details of a single page."""
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Display image
            try:
                img_path = Path(page.image_path)
                if img_path.exists():
                    image = Image.open(img_path)
                    st.image(image, use_column_width=True)
                else:
                    st.error("Image file not found.")
            except Exception as e:
                st.error(f"Error displaying image: {str(e)}")
                
        with col2:
            # Display text with edit option
            st.subheader("Extracted Text")
            
            # Initialize text area with current content
            current_text = page.text_content or ""
            new_text = st.text_area(
                "Text content", 
                value=current_text,
                height=400, 
                key=f"text_area_{page.id}"
            )
            
            # Save changes
            if new_text != current_text:
                if st.button("Save Text Changes", key=f"save_text_{page.id}"):
                    if self.entry_manager.update_page_text(page.id, new_text):
                        st.success("Text updated successfully.")
                        st.rerun()
                    else:
                        st.error("Failed to update text.")
                        
        # Delete page button
        if st.button("Delete Page", key=f"delete_page_{page.id}"):
            if self._delete_page(page.id):
                st.success("Page deleted successfully.")
                st.rerun()
            else:
                st.error("Failed to delete page.")
                
    def _show_add_page_form(self, entry_id):
        """Display a form to add a new page to an entry."""
        uploaded_file = st.file_uploader(
            "Upload an image of your journal page",
            type=["jpg", "jpeg", "png"],
            key=f"upload_page_{entry_id}"
        )
        
        if uploaded_file:
            # Preview the uploaded image
            image = Image.open(uploaded_file)
            st.image(image, width=300, caption="Preview")
            
            col1, col2 = st.columns(2)
            with col1:
                preprocess = st.checkbox("Preprocess image for better OCR", value=True)
                
            if st.button("Add Page"):
                with st.spinner("Processing image..."):
                    try:
                        # Save the uploaded file
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                            tmp.write(uploaded_file.getvalue())
                            tmp_path = tmp.name
                            
                        # Add the page
                        page_id = self.entry_manager.add_page_from_image(
                            entry_id=entry_id,
                            image_path=tmp_path,
                            preprocess=preprocess
                        )
                        
                        # Clean up
                        os.unlink(tmp_path)
                        
                        st.success("Page added successfully!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error adding page: {str(e)}")
                        
    def _show_new_entry_form(self):
        """Display a form to create a new entry."""
        st.header("Create New Journal Entry")
        
        with st.form("new_entry_form"):
            title = st.text_input("Title (optional)")
            
            col1, col2 = st.columns(2)
            with col1:
                date = st.date_input("Date", value=datetime.now())
            with col2:
                mood = st.text_input("Mood (optional)")
                
            tags = st.text_input("Tags (comma-separated, optional)")
            
            submitted = st.form_submit_button("Create Entry")
            
            if submitted:
                try:
                    # Process tags
                    tag_list = None
                    if tags:
                        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
                        
                    # Create the entry
                    entry_id = self.entry_manager.create_entry(
                        title=title if title else None,
                        date=datetime.combine(date, datetime.min.time()),
                        mood=mood if mood else None,
                        tags=tag_list
                    )
                    
                    st.success("Entry created successfully!")
                    
                    # Update state and redirect to edit the new entry
                    st.session_state.current_entry_id = entry_id
                    st.session_state.current_view = 'view'
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error creating entry: {str(e)}")
                    
    def _show_edit_entry_form(self):
        """Display a form to edit an existing entry."""
        if not st.session_state.current_entry_id:
            st.error("No entry selected")
            return
            
        entry = self.entry_manager.get_entry_with_pages(st.session_state.current_entry_id)
        
        if not entry:
            st.error("Entry not found")
            st.session_state.current_view = 'list'
            st.rerun()
            return
            
        st.header(f"Edit Entry: {entry.title or 'Untitled'}")
        
        with st.form("edit_entry_form"):
            # Current values
            current_title = entry.title or ""
            current_date = entry.date.date()
            current_mood = entry.mood or ""
            current_tags = ", ".join([tag.name for tag in entry.tags]) if entry.tags else ""
            
            # Form fields
            title = st.text_input("Title", value=current_title)
            
            col1, col2 = st.columns(2)
            with col1:
                date = st.date_input("Date", value=current_date)
            with col2:
                mood = st.text_input("Mood", value=current_mood)
                
            tags = st.text_input("Tags (comma-separated)", value=current_tags)
            
            submitted = st.form_submit_button("Update Entry")
            
            if submitted:
                try:
                    # Process tags
                    tag_list = None
                    if tags:
                        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
                        
                    # Update the entry
                    success = self.entry_manager.update_entry(
                        entry_id=entry.id,
                        title=title if title else None,
                        date=datetime.combine(date, datetime.min.time()),
                        mood=mood if mood else None,
                        tags=tag_list
                    )
                    
                    if success:
                        st.success("Entry updated successfully!")
                        st.session_state.current_view = 'view'
                        st.rerun()
                    else:
                        st.error("Failed to update entry.")
                        
                except Exception as e:
                    st.error(f"Error updating entry: {str(e)}")
                    
        # Provide option to go back to viewing
        if st.button("Cancel"):
            st.session_state.current_view = 'view'
            st.rerun()
            
    def _show_search_view(self):
        """Display the search interface."""
        st.header("Search Journal Entries")
        
        # Search form
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            query = st.text_input(
                "Search text", 
                value=st.session_state.search_query
            )
            
        with col2:
            # Get all tags for dropdown
            tags = self.db_manager.get_all_tags()
            tag_options = [""] + [tag.name for tag in tags]
            
            selected_tag = st.selectbox(
                "Filter by tag",
                options=tag_options,
                index=tag_options.index(st.session_state.search_tag) if st.session_state.search_tag in tag_options else 0
            )
            
        with col3:
            st.write("")  # Spacing
            search_clicked = st.button("Search")
            
        # Update session state
        st.session_state.search_query = query
        st.session_state.search_tag = selected_tag
        
        # Execute search
        if search_clicked or query or selected_tag:
            with st.spinner("Searching..."):
                entries = self.entry_manager.search_entries(
                    query=query if query else None,
                    tag=selected_tag if selected_tag else None
                )
                
            # Display results
            if entries:
                st.subheader(f"Found {len(entries)} results")
                
                # Create a column display
                for i in range(0, len(entries), 2):
                    cols = st.columns(2)
                    
                    for j in range(2):
                        idx = i + j
                        if idx < len(entries):
                            entry = entries[idx]
                            with cols[j]:
                                self._display_search_result(entry, query)
            else:
                st.info("No matching entries found.")
                
    def _display_search_result(self, entry, query):
        """Display a search result card."""
        # Prepare data for display
        title = entry.title or "Untitled Entry"
        date_str = entry.date.strftime("%Y-%m-%d")
        tags = ", ".join([tag.name for tag in entry.tags]) if entry.tags else "No tags"
        
        # Create card with border
        with st.container(border=True):
            # Title and date
            st.subheader(title)
            st.caption(f"Date: {date_str}")
            
            # Tags
            st.write(f"Tags: {tags}")
            
            # Text snippet if query exists
            if query:
                for page in entry.pages:
                    if page.text_content and query.lower() in page.text_content.lower():
                        snippet = self._get_text_snippet(page.text_content, query)
                        st.text_area(
                            f"Page {page.page_number}",
                            value=f"...{snippet}...",
                            height=100,
                            disabled=True,
                            key=f"snippet_{entry.id}_{page.page_number}"
                        )
                        break
                        
            # View button
            if st.button("View Entry", key=f"view_search_{entry.id}"):
                st.session_state.current_entry_id = entry.id
                st.session_state.current_view = 'view'
                st.rerun()
                
    def _get_text_snippet(self, text: str, query: str, context_chars: int = 100) -> str:
        """Extract a snippet of text around the query term."""
        query_lower = query.lower()
        text_lower = text.lower()
        
        pos = text_lower.find(query_lower)
        if pos == -1:
            return text[:200]  # Fallback if query not found
            
        start = max(0, pos - context_chars)
        end = min(len(text), pos + len(query) + context_chars)
        
        return text[start:end]
        
    def _show_stats_view(self):
        """Display journal statistics."""
        st.header("Journal Statistics")
        
        try:
            session = self.db_manager.get_session()
            
            try:
                from ..database.models import Entry, Page, Tag
                from sqlalchemy import func
                
                # Get counts
                entry_count = session.query(func.count(Entry.id)).scalar()
                page_count = session.query(func.count(Page.id)).scalar()
                tag_count = session.query(func.count(Tag.id)).scalar()
                
                # Get date range
                first_entry = session.query(func.min(Entry.date)).scalar()
                last_entry = session.query(func.max(Entry.date)).scalar()
                
                # Get most used tags
                tags = session.query(
                    Tag.name, func.count(Entry.id).label('count')
                ).join(
                    Tag.entries
                ).group_by(
                    Tag.name
                ).order_by(
                    func.count(Entry.id).desc()
                ).limit(10).all()
                
                # Get entries per month
                entries_by_month = session.query(
                    func.strftime('%Y-%m', Entry.date).label('month'),
                    func.count(Entry.id).label('count')
                ).group_by(
                    'month'
                ).order_by(
                    'month'
                ).all()
                
                # Display basic stats in columns
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Entries", entry_count)
                
                with col2:
                    st.metric("Total Pages", page_count)
                    
                with col3:
                    st.metric("Total Tags", tag_count)
                    
                with col4:
                    if entry_count > 0:
                        avg_pages = round(page_count / entry_count, 1)
                        st.metric("Avg. Pages per Entry", avg_pages)
                    else:
                        st.metric("Avg. Pages per Entry", 0)
                
                # Date range
                if first_entry and last_entry:
                    st.subheader("Journal Timeline")
                    st.write(f"First entry: {first_entry.strftime('%Y-%m-%d')}")
                    st.write(f"Last entry: {last_entry.strftime('%Y-%m-%d')}")
                    
                # Charts
                col1, col2 = st.columns(2)
                
                with col1:
                    # Top tags chart
                    if tags:
                        st.subheader("Most Used Tags")
                        
                        # Prepare data for chart
                        tag_data = pd.DataFrame(tags, columns=["Tag", "Count"])
                        st.bar_chart(tag_data.set_index("Tag"))
                        
                with col2:
                    # Entries by month chart
                    if entries_by_month:
                        st.subheader("Entries by Month")
                        
                        # Prepare data for chart
                        month_data = pd.DataFrame(entries_by_month, columns=["Month", "Count"])
                        st.line_chart(month_data.set_index("Month"))
                        
            finally:
                session.close()
                
        except Exception as e:
            st.error(f"Error getting statistics: {str(e)}")
            
    def _export_entry(self, entry, format_type):
        """Export an entry and provide download link."""
        try:
            if format_type == 'md':
                output_path = self.exporter.to_markdown(entry)
                
                # Read the file
                with open(output_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Offer download
                st.download_button(
                    label="Download Markdown File",
                    data=content,
                    file_name=output_path.name,
                    mime="text/markdown"
                )
                
            elif format_type == 'pdf':
                output_path = self.exporter.to_pdf(entry)
                
                # Read the file
                with open(output_path, 'rb') as f:
                    content = f.read()
                    
                # Offer download
                st.download_button(
                    label="Download PDF File",
                    data=content,
                    file_name=output_path.name,
                    mime="application/pdf"
                )
                
            st.success(f"Entry exported successfully!")
            
        except Exception as e:
            st.error(f"Error exporting entry: {str(e)}")
            
    def _delete_entry(self, entry_id):
        """Delete an entry with confirmation."""
        # Get entry to confirm
        entry = self.entry_manager.get_entry_with_pages(entry_id)
        
        if not entry:
            st.error(f"Entry with ID {entry_id} not found.")
            return False
            
        # Confirm deletion
        title = entry.title or "Untitled Entry"
        date_str = entry.date.strftime("%Y-%m-%d")
        
        confirm = st.checkbox(
            f"Confirm deletion of '{title}' from {date_str}?", 
            key=f"confirm_delete_{entry_id}"
        )
        
        if confirm:
            try:
                success = self.entry_manager.delete_entry(entry_id)
                
                if success:
                    st.success("Entry deleted successfully.")
                    if st.session_state.current_entry_id == entry_id:
                        st.session_state.current_entry_id = None
                    return True
                else:
                    st.error("Failed to delete entry.")
                    return False
                    
            except Exception as e:
                st.error(f"Error deleting entry: {str(e)}")
                return False
                
        return False
        
    def _delete_page(self, page_id):
        """Delete a page from the database."""
        try:
            session = self.db_manager.get_session()
            
            try:
                from ..database.models import Page
                
                # Get page to delete
                page = session.query(Page).filter_by(id=page_id).first()
                
                if not page:
                    return False
                    
                # Remember image path for cleanup
                image_path = page.image_path
                
                # Delete from database
                session.delete(page)
                session.commit()
                
                # Clean up image file
                if image_path and os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                    except Exception as e:
                        logger.error(f"Error deleting image file: {str(e)}")
                        
                return True
                
            except Exception as e:
                session.rollback()
                logger.error(f"Error deleting page: {str(e)}")
                raise
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error in delete_page: {str(e)}")
            return False

def run_streamlit_app():
    """Run the Streamlit app."""
    app = StreamlitApp()
    app.run()

if __name__ == "__main__":
    run_streamlit_app()