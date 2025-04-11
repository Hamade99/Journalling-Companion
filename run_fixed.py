import os
import sys
import streamlit as st
from pathlib import Path
from datetime import datetime
import tempfile
from PIL import Image
import shutil
import uuid

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Import the exact models and components
from digitized_journal.database.db_interface import DatabaseManager
from digitized_journal.database.models import Entry, Page, Tag
from digitized_journal.ocr.ocr_engine import OCREngine
from digitized_journal.config import IMAGES_DIR, DATA_DIR

# Ensure data directories exist
os.makedirs(IMAGES_DIR, exist_ok=True)

# Initialize database
db_manager = DatabaseManager()
db_manager.initialize_database()
ocr_engine = OCREngine()

# Page title
st.title("Digital Journal")

# Set up session state
if 'current_entry_id' not in st.session_state:
    st.session_state.current_entry_id = None
if 'view' not in st.session_state:
    st.session_state.view = 'list'

# Sidebar navigation
with st.sidebar:
    st.header("Navigation")
    if st.button("New Entry"):
        st.session_state.view = 'new'
        st.rerun()
    if st.button("All Entries"):
        st.session_state.view = 'list'
        st.rerun()

# Display based on view state
if st.session_state.view == 'list':
    # List all entries
    st.header("Journal Entries")
    session = db_manager.get_session()
    try:
        entries = session.query(Entry).order_by(Entry.date.desc()).all()
        
        if not entries:
            st.info("No entries found. Create your first entry!")
        else:
            for entry in entries:
                with st.container(border=True):
                    st.subheader(entry.title or "Untitled Entry")
                    st.caption(f"Date: {entry.date.strftime('%Y-%m-%d')}")
                    if st.button("View", key=f"view_{entry.id}"):
                        st.session_state.current_entry_id = entry.id
                        st.session_state.view = 'view'
                        st.rerun()
    finally:
        session.close()

elif st.session_state.view == 'new':
    # Create new entry
    st.header("Create New Entry")
    with st.form("new_entry_form"):
        title = st.text_input("Title")
        date = st.date_input("Date", value=datetime.now())
        mood = st.text_input("Mood (optional)")
        tags = st.text_input("Tags (comma-separated)")
        
        submitted = st.form_submit_button("Create Entry")
        
        if submitted:
            session = db_manager.get_session()
            try:
                # Create entry
                entry = Entry(
                    title=title if title else None,
                    date=datetime.combine(date, datetime.min.time()),
                    mood=mood if mood else None
                )
                
                # Process tags
                if tags:
                    tag_list = [t.strip() for t in tags.split(',') if t.strip()]
                    for tag_name in tag_list:
                        tag = session.query(Tag).filter_by(name=tag_name).first()
                        if not tag:
                            tag = Tag(name=tag_name)
                            session.add(tag)
                        entry.tags.append(tag)
                
                session.add(entry)
                session.commit()
                
                # Set as current entry
                st.session_state.current_entry_id = entry.id
                st.session_state.view = 'view'
                st.success("Entry created successfully!")
                st.rerun()
            finally:
                session.close()

elif st.session_state.view == 'view' and st.session_state.current_entry_id:
    # View an entry
    entry_id = st.session_state.current_entry_id
    session = db_manager.get_session()
    
    try:
        # Load entry
        entry = session.query(Entry).filter_by(id=entry_id).first()
        
        if not entry:
            st.error("Entry not found")
        else:
            st.header(entry.title or "Untitled Entry")
            st.subheader(f"Date: {entry.date.strftime('%Y-%m-%d')}")
            
            # Load all pages for this entry
            pages = session.query(Page).filter_by(entry_id=entry_id).order_by(Page.page_number).all()
            
            # Show pages
            if pages:
                st.subheader("Pages")
                for page in pages:
                    with st.expander(f"Page {page.page_number}"):
                        try:
                            img_path = Path(page.image_path)
                            if img_path.exists():
                                image = Image.open(img_path)
                                st.image(image, width=400)
                        except Exception as e:
                            st.error(f"Error displaying image: {str(e)}")
                        
                        st.text_area("Text Content", page.text_content or "", height=200, key=f"text_{page.id}")
            else:
                st.info("This entry has no pages yet.")
            
            # Add new page form
            st.subheader("Add New Page")
            uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
            
            if uploaded_file:
                # Preview
                image = Image.open(uploaded_file)
                st.image(image, width=300, caption="Preview")
                
                preprocess = st.checkbox("Preprocess image", value=True)
                
                if st.button("Add Page"):
                    with st.spinner("Processing..."):
                        try:
                            # Save temp file
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                                tmp.write(uploaded_file.getvalue())
                                tmp_path = tmp.name
                            
                            # Create directory for entry
                            entry_dir = IMAGES_DIR / str(entry_id)
                            entry_dir.mkdir(exist_ok=True)
                            
                            # Copy image with unique name
                            image_filename = f"{uuid.uuid4()}{Path(tmp_path).suffix}"
                            target_path = entry_dir / image_filename
                            shutil.copy2(tmp_path, target_path)
                            
                            # Extract text via OCR
                            try:
                                text_content = ocr_engine.process_image(target_path, preprocess=preprocess)
                            except Exception as e:
                                st.warning(f"OCR failed: {str(e)}")
                                text_content = ""
                            
                            # Get next page number
                            existing_pages = session.query(Page).filter_by(entry_id=entry_id).count()
                            page_number = existing_pages + 1
                            
                            # Create page
                            new_page = Page(
                                entry_id=entry_id,
                                page_number=page_number,
                                image_path=str(target_path),
                                text_content=text_content
                            )
                            session.add(new_page)
                            session.commit()
                            
                            # Clean up
                            os.unlink(tmp_path)
                            
                            st.success("Page added successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
    finally:
        session.close()