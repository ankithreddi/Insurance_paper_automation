import re
import json
import logging
import os
from typing import Union, Dict, Any, List
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(stream=sys.stdout), 
        logging.FileHandler("extraction.log", encoding='utf-8')  
    ]
)
logger = logging.getLogger(__name__)

def clean_text(text: Union[str, Any]) -> Union[str, Any]:
    """
    Clean extracted text by removing unwanted characters and formatting.
    """
    logger.debug("Starting text cleaning for value: %s", str(text)[:100] + "..." if len(str(text)) > 100 else str(text))
    
    if not isinstance(text, str):
        logger.debug("Value is not a string, returning as-is")
        return text
    
    original_text = text
    text = text.strip()
    
    if not text:
        logger.debug("Empty string after stripping")
        return text
    
    # Replace newlines and multiple spaces
    text = ' '.join(text.split())
    logger.debug("After whitespace normalization: %s", text)
    
    # Remove specific unwanted characters
    unwanted_chars = {
        '\u00a0': ' ',  # Non-breaking space
        '\u200b': '',    # Zero-width space
        '\u202f': ' ',   # Narrow no-break space
        '\ufeff': '',    # Byte order mark
        '\u200e': '',    # Left-to-right mark
        '\u200f': '',    # Right-to-left mark
    }
    
    for char, replacement in unwanted_chars.items():
        if char in text:
            text = text.replace(char, replacement)
            logger.debug("Removed special character %r: %s", char, text)
    
    # Remove leading punctuation
    while text and text[0] in ('-', ':', '.', ','):
        text = text[1:].strip()
        logger.debug("Removed leading punctuation: %s", text)
    
    if original_text != text:
        logger.info("Cleaned text: Before: %r, After: %r", original_text, text)
    
    return text

def clean_nested_data(data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
    """
    Recursively clean all string values in nested data structures.
    """
    logger.debug("Cleaning nested data structure: %s", type(data).__name__)
    
    if isinstance(data, dict):
        logger.debug("Processing dictionary with %d items", len(data))
        return {k: clean_nested_data(v) for k, v in data.items()}
    elif isinstance(data, (list, tuple)):
        logger.debug("Processing list/tuple with %d items", len(data))
        return [clean_nested_data(item) for item in data]
    
    result = clean_text(data)
    if result != data:
        logger.debug("Cleaned value changed: %r -> %r", data, result)
    return result

def load_regex_patterns(file_path: str) -> Dict:
    """Load regex patterns from JSON file with proper handling of escape characters."""
    logger.info("⏳ Loading regex patterns from: %s", file_path)
    
    if not os.path.exists(file_path):
        logger.error("❌ regex_patterns.json file not found at %s", file_path)
        return {}
    
    try:
        with open(file_path, "r") as file:
            content = file.read()
            logger.debug("Successfully read file content (%d bytes)", len(content))
            
            def parse_regex(dct):
                logger.debug("Processing dictionary with %d keys", len(dct))
                for key, value in dct.items():
                    if isinstance(value, dict):
                        logger.debug("Found nested dict at key: %s", key)
                        parse_regex(value)
                    elif isinstance(value, list):
                        logger.debug("Processing list at key: %s (%d items)", key, len(value))
                        for i, item in enumerate(value):
                            if isinstance(item, str) and item.startswith('r"'):
                                original = value[i]
                                value[i] = item[2:-1].replace('\\', '\\\\')
                                logger.debug("Converted raw string pattern: %r -> %r", original, value[i])
                return dct
            
            patterns = json.loads(content, object_hook=parse_regex)
            logger.info("✅ Successfully loaded regex patterns (%d companies)", len(patterns))
            return patterns
            
    except json.JSONDecodeError as e:
        logger.error("❌ Error parsing JSON file: %s", str(e))
        logger.debug("File content that caused error: %s", content[:200] + "..." if len(content) > 200 else content)
        return {}
    except Exception as e:
        logger.error("❌ Unexpected error loading regex patterns: %s", str(e), exc_info=True)
        return {}

file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "regex_patterns.json")
logger.info("🔎 Locating regex patterns file at: %s", file_path)
REGEX_PATTERNS = load_regex_patterns(file_path)

def extract_fields(text: str, company_name: str, policy_type: str) -> Dict:
    """
    Extract and clean structured data fields from policy documents using regex patterns.
    """
    logger.info("🚀 Starting extraction process for %s (%s)", company_name, policy_type)
    logger.debug("Input text length: %d characters", len(text))
    
    extracted_data = {}
    logger.info("🔍 Extracting fields for Company: %s | Policy Type: %s", company_name, policy_type)

    # Normalize input
    company_name_lower = company_name.lower().strip()
    policy_type_lower = policy_type.lower().strip()
    logger.debug("Normalized identifiers - Company: %r, Policy: %r", company_name_lower, policy_type_lower)

    # Validate company and policy type
    if company_name_lower not in REGEX_PATTERNS:
        logger.error("❌ Unsupported Company: %s (Available: %s)", 
                company_name, ", ".join(REGEX_PATTERNS.keys()))
        return {"error": f"Unsupported company: {company_name}"}

    if policy_type_lower not in REGEX_PATTERNS[company_name_lower]:
        available_types = list(REGEX_PATTERNS[company_name_lower].keys())
        logger.error("❌ Unsupported Policy Type: %s for Company: %s (Available: %s)", 
                policy_type, company_name, ", ".join(available_types))
        return {"error": f"Unsupported policy type: {policy_type} for company: {company_name}"}

    # Load regex patterns
    regex_patterns = REGEX_PATTERNS[company_name_lower][policy_type_lower]
    logger.info("📋 Loaded %d field patterns for %s/%s", 
            len(regex_patterns), company_name, policy_type)

    # Extract and clean fields
    for field, patterns in regex_patterns.items():
        logger.info("🔹 Processing field: %s (%d patterns)", field, len(patterns))
        matches = []

        for i, pattern in enumerate(patterns, 1):
            try:
                logger.debug("Trying pattern %d/%d for %s: %s", i, len(patterns), field, pattern)
                match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
                
                if match:
                    extracted_value = match.group(1)
                    logger.debug("Raw extracted value: %r", extracted_value)
                    
                    cleaned_value = clean_text(extracted_value)
                    matches.append(cleaned_value)
                    
                    logger.info("   ✅ Pattern %d matched: %r -> %r", i, extracted_value, cleaned_value)
                    logger.debug("Match details: %s", match)
                    break  # Stop after first match
                else:
                    logger.debug("   ❌ Pattern %d did not match", i)
                    
            except re.error as e:
                logger.error("   🛑 Regex error for pattern %d (%r): %s", i, pattern, str(e))
                logger.debug("Full pattern that caused error: %s", pattern)

        extracted_data[field] = {
            field.replace("_", " ").title(): matches[0] if matches else "Not Found"
        }
        logger.debug("Stored result for %s: %r", field, extracted_data[field])

    # Final deep clean of all extracted data
    logger.info("🧹 Performing final data cleaning pass")
    cleaned_data = clean_nested_data(extracted_data)
    
    # Logging extraction summary
    found_fields = sum(1 for v in cleaned_data.values() if v != "Not Found")
    logger.info("📊 Extraction complete - %d/%d fields found (%.1f%%)", 
            found_fields, len(regex_patterns), 
            (found_fields/len(regex_patterns))*100)
    
    logger.info("📌 Final Extracted Data:\n%s", json.dumps(cleaned_data, indent=4))
    return cleaned_data