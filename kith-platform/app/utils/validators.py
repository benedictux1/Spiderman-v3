from typing import NamedTuple, Any, Dict

class ValidationResult(NamedTuple):
    is_valid: bool
    error: str = None

def validate_note_input(data: Dict[str, Any]) -> ValidationResult:
    """Validate note processing input"""
    if not data:
        return ValidationResult(False, "No data provided")
    
    if 'contact_id' not in data:
        return ValidationResult(False, "contact_id is required")
    
    if 'content' not in data:
        return ValidationResult(False, "content is required")
    
    if not isinstance(data['contact_id'], int) or data['contact_id'] <= 0:
        return ValidationResult(False, "contact_id must be a positive integer")
    
    if not isinstance(data['content'], str) or not data['content'].strip():
        return ValidationResult(False, "content must be a non-empty string")
    
    if len(data['content'].strip()) < 10:
        return ValidationResult(False, "content must be at least 10 characters long")
    
    return ValidationResult(True)

def validate_contact_input(data: Dict[str, Any]) -> ValidationResult:
    """Validate contact creation/update input"""
    if not data:
        return ValidationResult(False, "No data provided")
    
    if 'full_name' not in data:
        return ValidationResult(False, "full_name is required")
    
    if not isinstance(data['full_name'], str) or not data['full_name'].strip():
        return ValidationResult(False, "full_name must be a non-empty string")
    
    if 'tier' in data:
        if not isinstance(data['tier'], int) or data['tier'] not in [1, 2]:
            return ValidationResult(False, "tier must be 1 or 2")
    
    return ValidationResult(True)
