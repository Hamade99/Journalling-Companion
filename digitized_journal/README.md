# Digital Journal with OCR

A Python application that allows users to digitize handwritten journal entries using OCR (Optical Character Recognition). The application can extract text from photos of handwritten journal pages, organize entries with multiple pages, and provide a searchable archive of journal content.

## Features

- **Image Processing & OCR**: Upload photos of handwritten journal pages and extract text using Tesseract OCR
- **Entry & Page Management**: Organize journal entries with multiple pages, edit extracted text
- **Tagging & Metadata**: Add titles, tags, dates, and mood indicators to entries
- **Full-Text Search**: Search across all journal entries
- **Export Options**: Export entries to Markdown or PDF formats
- **Multiple Interfaces**: Use either command-line or web interface (Streamlit)

## Requirements

- Python 3.7 or higher
- Tesseract OCR engine installed ([Installation instructions](https://github.com/tesseract-ocr/tesseract))
- Dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/digitized_journal.git
   cd digitized_journal
   ```

2. Install Tesseract OCR engine:
   - On Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
   - On macOS: `brew install tesseract`
   - On Windows: Download and install from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

3. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Install the package in development mode:
   ```
   pip install -e .
   ```

## Usage

### Command-Line Interface

Run the application in CLI mode:

```
python -m digitized_journal.main --cli
```

or simply:

```
journal --cli
```

This opens an interactive command prompt with the following commands:
- `new` - Create a new journal entry
- `add_page` - Add a page to an entry
- `list` - List all journal entries
- `view` - View a specific entry
- `search` - Search for entries
- `edit` - Edit an entry
- `export` - Export an entry (md or pdf)
- `delete` - Delete an entry
- `stats` - Show journal statistics
- `help` - Display help information

### Web Interface

Run the application with the Streamlit web interface:

```
python -m digitized_journal.main --web
```

or:

```
journal --web
```

This launches a web browser interface with an intuitive UI for managing journal entries.

## Project Structure

The application follows a modular architecture:

```
digitized_journal/
│
├── ocr/                # Image preprocessing and OCR
│   ├── preprocessor.py # Image preprocessing for better OCR results
│   └── ocr_engine.py   # Tesseract wrapper for text extraction
│
├── database/           # Database models and interactions
│   ├── models.py       # SQLAlchemy models
│   └── db_interface.py # Database operations
│
├── entries/            # Entry management
│   ├── entry_manager.py # Business logic for entries
│   └── exporter.py     # Export functionality (Markdown, PDF)
│
├── ui/                 # User interfaces
│   ├── cli.py          # Command-line interface
│   └── streamlit_app.py # Web interface
│
├── utils/              # Utilities
│   └── file_utils.py   # File operations, image handling
│
├── tests/              # Unit tests
├── main.py             # Application entry point
└── config.py           # Configuration settings
```

## Configuration

Configuration settings can be modified in `digitized_journal/config.py`, including:
- Database location
- Image storage paths
- OCR settings
- Export settings
- Logging configuration

## Extending the Application

The modular architecture makes it easy to extend the application with new features:

1. **New Export Formats**: Add new export methods to `exporter.py`
2. **Sentiment Analysis**: Create a new module for text analysis
3. **Cloud Synchronization**: Implement a sync module for cloud storage services
4. **Voice Notes**: Add audio recording and transcription capabilities
5. **Advanced Visualization**: Enhance the web UI with more visualizations

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for text recognition
- [SQLAlchemy](https://www.sqlalchemy.org/) for database operations
- [Streamlit](https://streamlit.io/) for the web interface
- [OpenCV](https://opencv.org/) for image processing