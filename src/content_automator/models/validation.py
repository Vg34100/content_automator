# metadata_validator.py
from typing import Dict, Any
import re
from utils.helpers import log_error

class MetadataValidator:
    @staticmethod
    def validate_title(title: str) -> bool:
        """Validate video title."""
        if not isinstance(title, str):
            log_error("Title must be a string")
            return False
        
        if not 5 <= len(title) <= 100:
            log_error("Title must be between 5 and 100 characters")
            return False
        
        return True
    
    @staticmethod
    def validate_description(desc: str) -> bool:
        """Validate video description."""
        if not isinstance(desc, str):
            log_error("Description must be a string")
            return False
            
        if len(desc) > 5000:
            log_error("Description exceeds YouTube's 5000 character limit")
            return False
            
        return True
    
    @staticmethod
    def validate_tags(tags: list) -> bool:
        """Validate video tags."""
        if not isinstance(tags, list):
            log_error("Tags must be a list")
            return False
            
        if len(tags) > 500:
            log_error("Too many tags (max 500)")
            return False
            
        for tag in tags:
            if not isinstance(tag, str):
                log_error("All tags must be strings")
                return False
            if len(tag) > 100:
                log_error(f"Tag '{tag}' exceeds 100 character limit")
                return False
                
        return True
    
    @classmethod
    def validate_metadata(cls, metadata: Dict[str, Any]) -> bool:
        """Validate all metadata fields."""
        required_fields = ['title', 'description', 'tags']
        
        for field in required_fields:
            if field not in metadata:
                log_error(f"Missing required field: {field}")
                return False
        
        return all([
            cls.validate_title(metadata['title']),
            cls.validate_description(metadata['description']),
            cls.validate_tags(metadata['tags'])
        ])