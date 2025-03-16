"""Configuration module for RecruitX.

This module contains configuration classes and settings for the RecruitX system.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional

@dataclass
class Config:
    """Main configuration class for RecruitX."""
    
    # API settings
    api_keys: Dict[str, str] = field(default_factory=dict)
    api_base_url: str = "https://api.recruitx.ai"
    api_timeout: int = 30
    
    # Model settings
    model_path: Optional[Path] = None
    model_version: str = "latest"
    model_cache_size: int = 1024
    
    # Security settings
    jwt_secret: Optional[str] = None
    token_expiry: int = 3600  # 1 hour
    encryption_key: Optional[str] = None
    
    # UI settings
    theme_mode: str = "light"
    animation_enabled: bool = True
    font_size: str = "medium"
    
    # Test settings
    test_data_path: Optional[Path] = None
    test_timeout: int = 60
    parallel_tests: bool = True
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[Path] = None
    
    def __post_init__(self):
        """Ensure necessary directories exist."""
        if self.model_path:
            self.model_path = Path(self.model_path)
            self.model_path.mkdir(parents=True, exist_ok=True)
            
        if self.test_data_path:
            self.test_data_path = Path(self.test_data_path)
            self.test_data_path.mkdir(parents=True, exist_ok=True)
            
        if self.log_file:
            self.log_file = Path(self.log_file)
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'Config':
        """Create a Config instance from a dictionary."""
        return cls(**config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Config instance to a dictionary."""
        return {
            'api_keys': self.api_keys,
            'api_base_url': self.api_base_url,
            'api_timeout': self.api_timeout,
            'model_path': str(self.model_path) if self.model_path else None,
            'model_version': self.model_version,
            'model_cache_size': self.model_cache_size,
            'jwt_secret': self.jwt_secret,
            'token_expiry': self.token_expiry,
            'encryption_key': self.encryption_key,
            'theme_mode': self.theme_mode,
            'animation_enabled': self.animation_enabled,
            'font_size': self.font_size,
            'test_data_path': str(self.test_data_path) if self.test_data_path else None,
            'test_timeout': self.test_timeout,
            'parallel_tests': self.parallel_tests,
            'log_level': self.log_level,
            'log_file': str(self.log_file) if self.log_file else None
        } 