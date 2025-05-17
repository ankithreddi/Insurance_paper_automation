# PDF Data Extractor

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.7+-blue?style=for-the-badge&logo=python)

This api extracts structured data from PDF documents (or ZIP archives containing PDFs) using regular expressions. It's designed to process insurance policy documents and extract key fields like policy numbers, customer information, dates, and financial details etc--.

## Features

- Extract text from PDF files
- Process multiple PDFs in a ZIP archive
- Extract structured data using configurable regex patterns
- REST API endpoint for easy integration
- Detailed logging for debugging

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Application

Start the FastAPI server:
```bash
python run.py
```

The application will start on `http://localhost:8000` with automatic reload enabled.

Access the interactive API documentation:

Swagger UI: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc

### API Endpoints

- **GET /** - Welcome message
- **POST /pdf/extract** - Extract data from PDF or ZIP file

### Making Requests

To extract data from a PDF file:

```bash
curl -X POST -F "file=@example.pdf" http://localhost:8000/pdf/extract
```

To extract data from a ZIP file containing PDFs:

```bash
curl -X POST -F "file=@archive.zip" http://localhost:8000/pdf/extract
```

### Configuration

Regex patterns for data extraction can be modified in `app/config.py`.


## Project Structure

```
.
├── run.py                # Application entry point
├── app/
│   ├── main.py           # FastAPI application setup
│   ├── routes.py         # API routes
│   ├── config.py         # Regex pattern configuration
│   ├── services/
│   │   ├── pdf_service.py    # PDF text extraction
│   │   └── regex_service.py  # Data extraction using regex
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Dependencies

- FastAPI - Web framework
- Uvicorn - ASGI server
- pdfplumber - PDF text extraction
- Python 3.7+

## Limitations

- Currently optimized for specific insurance document formats
- Regex patterns may need adjustment for different document layouts
- Large PDF files may take longer to process

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements.

## License

[MIT License](LICENSE)