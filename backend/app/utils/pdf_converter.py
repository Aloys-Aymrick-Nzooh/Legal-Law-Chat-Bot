"""PDF to text conversion utilities."""

import io
from pathlib import Path
from typing import Union

import pdfplumber


def extract_text_from_pdf(file_content: Union[bytes, io.BytesIO]) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        file_content: PDF file as bytes or BytesIO object
        
    Returns:
        Extracted text content
    """
    if isinstance(file_content, bytes):
        file_content = io.BytesIO(file_content)
    
    text_parts = []
    
    with pdfplumber.open(file_content) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    
    return "\n\n".join(text_parts)


def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """
    Extract text from a file based on its extension.
    
    Args:
        file_content: File content as bytes
        filename: Original filename to determine type
        
    Returns:
        Extracted text content
    """
    extension = Path(filename).suffix.lower()
    
    if extension == ".pdf":
        return extract_text_from_pdf(file_content)
    elif extension in [".txt", ".md", ".text"]:
        return file_content.decode("utf-8", errors="ignore")
    else:
        # Try to decode as text
        try:
            return file_content.decode("utf-8", errors="ignore")
        except Exception:
            raise ValueError(f"Unsupported file type: {extension}")


def clean_text(text: str) -> str:
    """
    Clean extracted text.
    
    Args:
        text: Raw extracted text
        
    Returns:
        Cleaned text
    """
    # Remove excessive whitespace
    lines = text.split("\n")
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)
    
    # Join with single newlines, collapse multiple blank lines
    result = "\n".join(cleaned_lines)
    
    # Collapse multiple newlines to double newlines
    while "\n\n\n" in result:
        result = result.replace("\n\n\n", "\n\n")
    
    return result
