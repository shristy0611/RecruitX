import hashlib
import json
from typing import Dict, Any, Optional, Union, List
import os
from pathlib import Path

def generate_content_hash(content: Union[str, bytes, Dict, List]) -> str:
    """Generate a hash from content for deduplication
    
    Args:
        content: Content to hash (string, bytes, or serializable object)
        
    Returns:
        SHA-256 hash of the content
    """
    if isinstance(content, (dict, list)):
        # Convert to JSON string with sorted keys for consistent hashing
        content = json.dumps(content, sort_keys=True)
    
    if isinstance(content, str):
        content = content.encode('utf-8')
        
    return hashlib.sha256(content).hexdigest()

def extract_file_metadata(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Extract metadata from a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dict containing file metadata
    """
    path = Path(file_path)
    
    return {
        'file_name': path.name,
        'file_extension': path.suffix.lower(),
        'file_size': path.stat().st_size if path.exists() else 0,
        'last_modified': path.stat().st_mtime if path.exists() else None,
    }

def normalize_document_type(file_extension: str) -> str:
    """Normalize document type based on file extension
    
    Args:
        file_extension: File extension (e.g., '.pdf', '.docx')
        
    Returns:
        Normalized document type
    """
    extension = file_extension.lower()
    
    if extension in ['.pdf']:
        return 'pdf'
    elif extension in ['.docx', '.doc']:
        return 'word'
    elif extension in ['.txt', '.md', '.rst']:
        return 'text'
    elif extension in ['.json']:
        return 'json'
    elif extension in ['.csv', '.xlsx', '.xls']:
        return 'spreadsheet'
    else:
        return 'unknown'
        
def serialize_metadata(metadata: Dict[str, Any]) -> str:
    """Serialize metadata to JSON string
    
    Args:
        metadata: Metadata dict
        
    Returns:
        JSON string
    """
    return json.dumps(metadata, default=str)

def deserialize_metadata(metadata_str: str) -> Dict[str, Any]:
    """Deserialize metadata from JSON string
    
    Args:
        metadata_str: JSON string
        
    Returns:
        Metadata dict
    """
    if not metadata_str:
        return {}
    return json.loads(metadata_str)

def ensure_data_dir_exists() -> Path:
    """Ensure the data directory exists
    
    Returns:
        Path to the data directory
    """
    data_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "../../data"
    data_dir = data_dir.resolve()
    data_dir.mkdir(exist_ok=True)
    return data_dir 