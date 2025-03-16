"""Utility functions for RecruitX."""

import logging
import os
from pathlib import Path
from typing import Optional

def setup_logging(log_file: Optional[Path] = None, log_level: str = "INFO") -> None:
    """Set up logging configuration.
    
    Args:
        log_file: Optional path to the log file. If None, logs will only go to console.
        log_level: The logging level to use. Defaults to "INFO".
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=getattr(logging, log_level.upper()), format=log_format)
    
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)

def ensure_path_exists(path: str | Path) -> Path:
    """Create a directory path if it does not exist.
    
    Args:
        path: The path to create.
        
    Returns:
        The Path object for the created directory.
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_project_root() -> Path:
    """Get the absolute path to the project root directory.
    
    Returns:
        The Path object for the project root directory.
    """
    return Path(__file__).parent.parent.parent
