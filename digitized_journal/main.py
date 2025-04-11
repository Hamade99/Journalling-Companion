"""Main entry point for the Digital Journal application."""

import os
import sys
import argparse
import logging
from pathlib import Path

from digitized_journal.database.db_interface import DatabaseManager
from digitized_journal.ui.cli import JournalCLI
from digitized_journal.config import DATA_DIR, LOG_LEVEL, LOG_FILE

# Set up logging
def setup_logging():
    """Configure logging for the application."""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Configure logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Set up file handler
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=log_format,
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce verbosity of third-party libraries
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Digital Journal Application')
    
    parser.add_argument('--cli', action='store_true', help='Run in CLI mode')
    parser.add_argument('--web', action='store_true', help='Run in web interface mode')
    parser.add_argument('--init-db', action='store_true', help='Initialize the database only')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    return parser.parse_args()

def main():
    """Main entry point."""
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Digital Journal Application")
    
    # Parse command line arguments
    args = parse_args()
    
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.initialize_database()
    logger.info("Database initialized")
    
    if args.init_db:
        print("Database initialized successfully.")
        return
        
    # Choose interface based on arguments
    if args.web:
        # Use streamlit interface
        try:
            from digitized_journal.ui.streamlit_app import run_streamlit_app
            print("Starting web interface. Press Ctrl+C to exit.")
            run_streamlit_app()
        except ImportError:
            logger.error("Streamlit not installed. Please install with 'pip install streamlit'")
            print("Error: Streamlit not installed. Please install with 'pip install streamlit'")
            sys.exit(1)
    else:
        # Default to CLI
        cli = JournalCLI()
        try:
            cli.cmdloop()
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            # Ensure we clean up any database connections
            db_manager.close_sessions()

if __name__ == "__main__":
    main()