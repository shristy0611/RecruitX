import os
import fitz  # PyMuPDF
from docx import Document
from pathlib import Path
from typing import Optional, Dict, Any

class DocumentParser:
    """Parser for different document types (PDF, DOCX, etc.)"""
    
    @staticmethod
    def parse_document(file_path: str) -> Dict[str, Any]:
        """
        Parse a document and extract its text content.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dict containing:
            - text: Extracted text content
            - metadata: Document metadata
            - file_type: Type of the document
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        file_type = file_path.suffix.lower()
        
        if file_type == '.pdf':
            return DocumentParser._parse_pdf(file_path)
        elif file_type == '.docx':
            return DocumentParser._parse_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    @staticmethod
    def _parse_pdf(file_path: Path) -> Dict[str, Any]:
        """Parse a PDF document."""
        doc = fitz.open(file_path)
        text = ""
        metadata = doc.metadata
        
        for page in doc:
            text += page.get_text()
            
        doc.close()
        
        return {
            'text': text,
            'metadata': metadata,
            'file_type': '.pdf'
        }
    
    @staticmethod
    def _parse_docx(file_path: Path) -> Dict[str, Any]:
        """Parse a DOCX document."""
        doc = Document(file_path)
        text = ""
        
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
            
        metadata = {
            'author': doc.core_properties.author,
            'created': doc.core_properties.created,
            'modified': doc.core_properties.modified,
            'title': doc.core_properties.title
        }
        
        return {
            'text': text,
            'metadata': metadata,
            'file_type': '.docx'
        }
    
    @staticmethod
    def get_file_type(file_path: str) -> str:
        """Get the file type from the file extension."""
        return Path(file_path).suffix.lower()
    
    @staticmethod
    def is_supported_file_type(file_path: str) -> bool:
        """Check if the file type is supported."""
        supported_types = {'.pdf', '.docx'}
        return Path(file_path).suffix.lower() in supported_types 