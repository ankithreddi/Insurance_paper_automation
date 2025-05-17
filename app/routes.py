import io
import logging
import zipfile
from typing import Dict, Any

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse
from app.services.pdf_service import extract_text_from_pdf
from app.services.regex_service import extract_fields

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/extract",
    response_model=Dict[str, Any],
    summary="Extract data from PDF/ZIP",
    description="""
    ## Endpoint for extracting data from policy documents
    
    ### Features:
    - Processes single PDF files
    - Processes ZIP archives containing multiple PDFs
    - Returns extracted data in structured JSON format
    
    ### Supported Files:
    - PDF (.pdf)
    - ZIP (.zip) containing PDFs
-------------------------------------- 
    ### Example Requests:
    
    **1. Single PDF Request:**
    ```json
    {
      "company_name": "bajaj allianz", 
      "policy_type": "non-motor"
    }
    ```
    With PDF file attached
    -----------------------------------
     ```json
    {
      "company_name": "iffco tokio", 
      "policy_type": "motor"
    }
    ```
    With PDF file attached
-----------------------------------------
    **2. ZIP Archive Request:**
    ```json
    {
      "company_name": "iffco tokio",
      "policy_type": "non-motor"
    }
    ```
    With ZIP file containing multiple PDFs attached
    """,
    responses={
        200: {"description": "Successful extraction"},
        400: {"description": "Invalid file format"},
        500: {"description": "Internal server error"}
    }
)
async def extract_data(
    file: UploadFile = File(..., description="PDF or ZIP file to process."),
    company_name: str = Form(..., description="Name of the insurance company (e.g., 'bajaj allianz', 'iffco tokio')"),
    policy_type: str = Form(..., description="Type of insurance policy (e.g., 'motor', 'non-motor')")
):

    """
    Extract structured data from insurance policy documents.
    
    Args:
        file: Uploaded PDF or ZIP file containing PDFs
        company_name: Name of the insurance company
        policy_type: Type of insurance policy
        
    Returns:
        Dictionary with filename as key and extracted data as value
    """
    logger.info("Received request to extract data from file: %s", file.filename)
    logger.info("Company Name: %s | Policy Type: %s", company_name, policy_type)

    results = {}

    try:
        if file.filename.endswith(".pdf"):
            logger.info("Processing a single PDF file: %s", file.filename)
            pdf_bytes = await file.read()

            logger.info("Extracting text from PDF: %s", file.filename)
            extracted_text = extract_text_from_pdf(pdf_bytes)

            logger.info("Extracting structured fields from PDF text")
            results[file.filename] = extract_fields(extracted_text, company_name, policy_type)

            logger.info("Successfully processed PDF file: %s", file.filename)

        elif file.filename.endswith(".zip"):
            logger.info("Processing a ZIP file: %s", file.filename)
            zip_bytes = await file.read()
            zip_buffer = io.BytesIO(zip_bytes)

            with zipfile.ZipFile(zip_buffer, "r") as zip_file:
                pdf_files = [f for f in zip_file.namelist() if f.lower().endswith(".pdf")]
                logger.info("Found %d PDFs inside the ZIP file", len(pdf_files))

                for file_name in pdf_files:
                    try:
                        logger.info("Processing PDF from ZIP: %s", file_name)
                        with zip_file.open(file_name) as pdf_file:
                            pdf_bytes = pdf_file.read()

                            logger.info("Extracting text from PDF: %s", file_name)
                            extracted_text = extract_text_from_pdf(pdf_bytes)

                            logger.info("Extracting structured fields from PDF text")
                            results[file_name] = extract_fields(extracted_text, company_name, policy_type)

                            logger.info("Successfully processed PDF file: %s", file_name)
                    except Exception as e:
                        logger.error("Error processing file %s: %s", file_name, str(e))
                        results[file_name] = {"error": f"Failed to process file: {str(e)}"}

        else:
            logger.warning("Unsupported file format received: %s", file.filename)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF or ZIP files are supported."
            )

        logger.info("Extraction process completed successfully")
        return results

    except zipfile.BadZipFile:
        logger.exception("Invalid ZIP file provided: %s", file.filename)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ZIP file."
        )
        
    except Exception as e:
        logger.exception("Unexpected error processing file: %s - %s", file.filename, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the file."
        )