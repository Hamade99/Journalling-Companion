"""Command-line interface for the journal application."""

import os
import sys
import cmd
import glob
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict

from ..database.db_interface import DatabaseManager
from ..entries.entry_manager import EntryManager
from ..entries.exporter import EntryExporter
from ..utils.file_utils import verify_image_file
from ..config import DATA_DIR

logger = logging.getLogger(__name__)

class JournalCLI(cmd.Cmd):
    """Interactive command-line interface for the journal application."""
    
    intro = """
    Welcome to the Digital Journal Application!
    Type 'help' or '?' to list commands.
    """
    prompt = "journal> "
    
    def __init__(self):
        """Initialize the CLI with necessary components."""
        super().__init__()
        self.db_manager = DatabaseManager()
        self.db_manager.initialize_database()
        self.entry_manager = EntryManager(db_manager=self.db_manager)
        self.exporter = EntryExporter()
        self.current_entry_id = None
        
    def emptyline(self):
        """Do nothing on empty line."""
        pass
        
    def do_exit(self, arg):
        """Exit the application."""
        print("Goodbye!")
        return True
        
    def do_quit(self, arg):
        """Exit the application."""
        return self.do_exit(arg)
        
    def do_new(self, arg):
        """Create a new journal entry: new [title]"""
        title = arg.strip() if arg else None
        
        try:
            # Get additional metadata
            if not title:
                title = input("Title (optional): ").strip() or None
                
            date_str = input("Date (YYYY-MM-DD, empty for today): ").strip()
            if date_str:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                date = datetime.now()
                
            mood = input("Mood (optional): ").strip() or None
            
            tags_input = input("Tags (comma-separated, optional): ").strip()
            tags = [tag.strip() for tag in tags_input.split(',')] if tags_input else None
            
            # Create the entry
            entry_id = self.entry_manager.create_entry(
                title=title,
                date=date,
                mood=mood,
                tags=tags
            )
            
            self.current_entry_id = entry_id
            print(f"Created new entry with ID: {entry_id}")
            
            # Ask for images
            self._add_pages_interactive(entry_id)
            
        except Exception as e:
            print(f"Error creating entry: {str(e)}")
            
    def _add_pages_interactive(self, entry_id: int) -> None:
        """Interactive helper to add pages to an entry."""
        while True:
            add_page = input("Add a page? (y/n): ").lower().strip()
            if add_page != 'y':
                break
                
            # Get image path
            image_path = input("Enter image file path: ").strip()
            if not image_path:
                continue
                
            image_path = Path(image_path)
            if not image_path.exists():
                print(f"File not found: {image_path}")
                continue
                
            if not verify_image_file(image_path):
                print(f"Not a valid image file: {image_path}")
                continue
                
            try:
                page_id = self.entry_manager.add_page_from_image(
                    entry_id=entry_id,
                    image_path=image_path
                )
                print(f"Added page with ID: {page_id}")
            except Exception as e:
                print(f"Error adding page: {str(e)}")
                
    def do_add_page(self, arg):
        """Add a page to an entry: add_page <entry_id> <image_path>"""
        args = arg.split(maxsplit=1)
        
        if len(args) < 2:
            print("Usage: add_page <entry_id> <image_path>")
            return
            
        try:
            entry_id = int(args[0])
            image_path = Path(args[1].strip())
            
            if not image_path.exists():
                print(f"File not found: {image_path}")
                return
                
            if not verify_image_file(image_path):
                print(f"Not a valid image file: {image_path}")
                return
                
            page_id = self.entry_manager.add_page_from_image(
                entry_id=entry_id,
                image_path=image_path
            )
            print(f"Added page with ID: {page_id}")
            
        except ValueError:
            print("Invalid entry ID. Please provide a valid number.")
        except Exception as e:
            print(f"Error adding page: {str(e)}")
            
    def do_list(self, arg):
        """List all journal entries: list [limit]"""
        try:
            limit = int(arg) if arg.strip() else None
        except ValueError:
            print("Invalid limit. Please provide a valid number.")
            return
            
        try:
            entries = self.entry_manager.get_all_entries()
            
            if limit:
                entries = entries[:limit]
                
            if not entries:
                print("No entries found.")
                return
                
            print("\nJournal Entries:")
            print("=" * 60)
            
            for entry in entries:
                # Format date
                date_str = entry.date.strftime("%Y-%m-%d")
                
                # Format title with fallback
                title = entry.title or "(Untitled)"
                
                # Format tags
                tags_str = ", ".join(tag.name for tag in entry.tags) if entry.tags else ""
                
                # Format page count
                page_count = len(entry.pages)
                
                print(f"ID: {entry.id} | Date: {date_str} | Title: {title}")
                print(f"Pages: {page_count} | Tags: {tags_str}")
                print("-" * 60)
                
        except Exception as e:
            print(f"Error listing entries: {str(e)}")
            
    def do_view(self, arg):
        """View a specific entry: view <entry_id>"""
        if not arg.strip():
            print("Usage: view <entry_id>")
            return
            
        try:
            entry_id = int(arg)
            entry = self.entry_manager.get_entry_with_pages(entry_id)
            
            if not entry:
                print(f"Entry with ID {entry_id} not found.")
                return
                
            self.current_entry_id = entry_id
                
            print("\n" + "=" * 60)
            print(f"Entry ID: {entry.id}")
            print(f"Title: {entry.title or '(Untitled)'}")
            print(f"Date: {entry.date.strftime('%Y-%m-%d %H:%M')}")
            
            if entry.mood:
                print(f"Mood: {entry.mood}")
                
            if entry.tags:
                tags_str = ", ".join(tag.name for tag in entry.tags)
                print(f"Tags: {tags_str}")
                
            print("=" * 60)
            
            for page in entry.pages:
                print(f"\nPage {page.page_number}:")
                print(f"Image: {page.image_path}")
                print("-" * 60)
                if page.text_content:
                    print(page.text_content[:500] + "..." if len(page.text_content) > 500 else page.text_content)
                else:
                    print("(No text content)")
                print("-" * 60)
                
        except ValueError:
            print("Invalid entry ID. Please provide a valid number.")
        except Exception as e:
            print(f"Error viewing entry: {str(e)}")
            
    def do_search(self, arg):
        """Search for entries: search <query> [tag]"""
        if not arg.strip():
            print("Usage: search <query> [tag]")
            return
            
        try:
            parts = arg.split(maxsplit=1)
            query = parts[0].strip()
            
            # Check if there's a tag specified
            tag = None
            if len(parts) > 1 and ':' in parts[1]:
                tag_part = parts[1].strip()
                if tag_part.startswith("tag:"):
                    tag = tag_part[4:].strip()
                    
            entries = self.entry_manager.search_entries(query=query, tag=tag)
            
            if not entries:
                print("No matching entries found.")
                return
                
            print(f"\nFound {len(entries)} matching entries:")
            print("=" * 60)
            
            for entry in entries:
                # Format date
                date_str = entry.date.strftime("%Y-%m-%d")
                
                # Format title with fallback
                title = entry.title or "(Untitled)"
                
                # Format tags
                tags_str = ", ".join(tag.name for tag in entry.tags) if entry.tags else ""
                
                print(f"ID: {entry.id} | Date: {date_str} | Title: {title}")
                print(f"Tags: {tags_str}")
                
                # Show a snippet of text for context
                for page in entry.pages:
                    if page.text_content and query.lower() in page.text_content.lower():
                        snippet = self._get_text_snippet(page.text_content, query)
                        print(f"  Page {page.page_number}: ...{snippet}...")
                        break
                        
                print("-" * 60)
                
        except Exception as e:
            print(f"Error searching entries: {str(e)}")
            
    def _get_text_snippet(self, text: str, query: str, context_chars: int = 40) -> str:
        """Extract a snippet of text around the query term."""
        query_lower = query.lower()
        text_lower = text.lower()
        
        pos = text_lower.find(query_lower)
        if pos == -1:
            return text[:80]  # Fallback if query not found
            
        start = max(0, pos - context_chars)
        end = min(len(text), pos + len(query) + context_chars)
        
        return text[start:end]
        
    def do_edit(self, arg):
        """Edit an entry: edit <entry_id>"""
        if not arg.strip():
            print("Usage: edit <entry_id>")
            return
            
        try:
            entry_id = int(arg)
            entry = self.entry_manager.get_entry_with_pages(entry_id)
            
            if not entry:
                print(f"Entry with ID {entry_id} not found.")
                return
                
            print(f"\nEditing Entry (ID: {entry.id})")
            print("Press Enter to keep current values.\n")
            
            # Get current values for display
            current_title = entry.title or "(Untitled)"
            current_date = entry.date.strftime("%Y-%m-%d")
            current_mood = entry.mood or "(None)"
            current_tags = ", ".join(tag.name for tag in entry.tags) if entry.tags else "(None)"
            
            # Get new values
            new_title = input(f"Title [{current_title}]: ").strip()
            if not new_title:
                new_title = None  # Keep current
                
            new_date_str = input(f"Date [{current_date}]: ").strip()
            new_date = None
            if new_date_str:
                try:
                    new_date = datetime.strptime(new_date_str, "%Y-%m-%d")
                except ValueError:
                    print("Invalid date format. Using current date.")
                    
            new_mood = input(f"Mood [{current_mood}]: ").strip()
            if not new_mood:
                new_mood = None  # Keep current
                
            new_tags_str = input(f"Tags (comma-separated) [{current_tags}]: ").strip()
            new_tags = None
            if new_tags_str:
                new_tags = [tag.strip() for tag in new_tags_str.split(',')]
                
            # Update the entry
            success = self.entry_manager.update_entry(
                entry_id=entry_id,
                title=new_title,
                date=new_date,
                mood=new_mood,
                tags=new_tags
            )
            
            if success:
                print("Entry updated successfully.")
                
                # Ask if user wants to edit page text
                edit_pages = input("Edit page text? (y/n): ").lower().strip() == 'y'
                
                if edit_pages:
                    for page in entry.pages:
                        edit_this_page = input(f"Edit Page {page.page_number}? (y/n): ").lower().strip() == 'y'
                        
                        if edit_this_page:
                            print(f"\nCurrent text for Page {page.page_number}:")
                            print("-" * 60)
                            print(page.text_content or "(No text)")
                            print("-" * 60)
                            
                            print("Enter new text (end with a line containing only '.' (period)):")
                            new_text_lines = []
                            
                            while True:
                                line = input()
                                if line == ".":
                                    break
                                new_text_lines.append(line)
                                
                            if new_text_lines:
                                new_text = "\n".join(new_text_lines)
                                self.entry_manager.update_page_text(page.id, new_text)
                                print("Page text updated successfully.")
                            else:
                                print("No changes made to page text.")
            else:
                print("Failed to update entry.")
                
        except ValueError:
            print("Invalid entry ID. Please provide a valid number.")
        except Exception as e:
            print(f"Error editing entry: {str(e)}")
            
    def do_export(self, arg):
        """Export an entry: export <entry_id> [format=md|pdf]"""
        parts = arg.split()
        
        if not parts:
            print("Usage: export <entry_id> [format=md|pdf]")
            return
            
        try:
            entry_id = int(parts[0])
            
            # Default format is markdown
            format_type = "md"
            
            # Check if format is specified
            if len(parts) > 1:
                format_arg = parts[1].lower()
                if format_arg in ("md", "markdown"):
                    format_type = "md"
                elif format_arg in ("pdf"):
                    format_type = "pdf"
                else:
                    print(f"Unknown format: {format_arg}. Using markdown.")
                    
            # Get the entry
            entry = self.entry_manager.get_entry_with_pages(entry_id)
            
            if not entry:
                print(f"Entry with ID {entry_id} not found.")
                return
                
            # Export the entry
            if format_type == "md":
                output_path = self.exporter.to_markdown(entry)
                print(f"Entry exported to Markdown: {output_path}")
            else:  # pdf
                output_path = self.exporter.to_pdf(entry)
                print(f"Entry exported to PDF: {output_path}")
                
        except ValueError:
            print("Invalid entry ID. Please provide a valid number.")
        except Exception as e:
            print(f"Error exporting entry: {str(e)}")
            
    def do_delete(self, arg):
        """Delete an entry: delete <entry_id>"""
        if not arg.strip():
            print("Usage: delete <entry_id>")
            return
            
        try:
            entry_id = int(arg)
            
            # Get entry to confirm
            entry = self.entry_manager.get_entry_with_pages(entry_id)
            
            if not entry:
                print(f"Entry with ID {entry_id} not found.")
                return
                
            # Confirm deletion
            title = entry.title or "(Untitled)"
            date_str = entry.date.strftime("%Y-%m-%d")
            
            confirm = input(f"Are you sure you want to delete entry '{title}' from {date_str}? (y/n): ").lower().strip()
            
            if confirm != 'y':
                print("Deletion cancelled.")
                return
                
            # Delete the entry
            success = self.entry_manager.delete_entry(entry_id)
            
            if success:
                print("Entry deleted successfully.")
                if self.current_entry_id == entry_id:
                    self.current_entry_id = None
            else:
                print("Failed to delete entry.")
                
        except ValueError:
            print("Invalid entry ID. Please provide a valid number.")
        except Exception as e:
            print(f"Error deleting entry: {str(e)}")
            
    def do_stats(self, arg):
        """Show journal statistics."""
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
                ).limit(5).all()
                
                # Display statistics
                print("\nJournal Statistics:")
                print("=" * 50)
                print(f"Total Entries: {entry_count}")
                print(f"Total Pages: {page_count}")
                print(f"Total Tags: {tag_count}")
                
                if first_entry and last_entry:
                    print(f"Date Range: {first_entry.strftime('%Y-%m-%d')} to {last_entry.strftime('%Y-%m-%d')}")
                    
                if tags:
                    print("\nMost Used Tags:")
                    for tag_name, count in tags:
                        print(f"  {tag_name}: {count} entries")
                        
                print("=" * 50)
                
            finally:
                session.close()
                
        except Exception as e:
            print(f"Error getting statistics: {str(e)}")
            
    def do_help(self, arg):
        """Show help message."""
        if arg:
            # Show help for a specific command
            super().do_help(arg)
        else:
            # Show general help
            print("\nDigital Journal Application")
            print("\nAvailable commands:")
            print("  new                 - Create a new journal entry")
            print("  add_page            - Add a page to an entry")
            print("  list [limit]        - List all journal entries")
            print("  view <entry_id>     - View a specific entry")
            print("  search <query>      - Search for entries")
            print("  edit <entry_id>     - Edit an entry")
            print("  export <entry_id>   - Export an entry (md or pdf)")
            print("  delete <entry_id>   - Delete an entry")
            print("  stats               - Show journal statistics")
            print("  exit, quit          - Exit the application")
            print("\nType 'help <command>' for more detailed information.")