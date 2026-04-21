"""
Utility functions for the Project application.
"""

import os
import sys
import json
import logging
import hashlib
import datetime
import random
import string
from typing import Any, Dict, List, Optional, Union, Tuple
from pathlib import Path
from functools import wraps
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProjectError(Exception):
    """Base exception for Project-related errors."""
    pass


class ValidationError(ProjectError):
    """Raised when validation fails."""
    pass


class FileOperationError(ProjectError):
    """Raised when file operations fail."""
    pass


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Configure application logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def validate_path(path: Union[str, Path], must_exist: bool = True) -> Path:
    """
    Validate and convert a path string to Path object.
    
    Args:
        path: Path string or Path object
        must_exist: If True, raises error if path doesn't exist
        
    Returns:
        Path object
        
    Raises:
        ValidationError: If path validation fails
    """
    try:
        path_obj = Path(path) if isinstance(path, str) else path
        
        if must_exist and not path_obj.exists():
            raise ValidationError(f"Path does not exist: {path_obj}")
            
        return path_obj.resolve()
    except Exception as e:
        raise ValidationError(f"Invalid path '{path}': {str(e)}")


def read_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Read and parse JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON data as dictionary
        
    Raises:
        FileOperationError: If file cannot be read or parsed
    """
    try:
        path = validate_path(file_path, must_exist=True)
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        logger.debug(f"Successfully read JSON file: {path}")
        return data
    except json.JSONDecodeError as e:
        raise FileOperationError(f"Invalid JSON in file {file_path}: {str(e)}")
    except Exception as e:
        raise FileOperationError(f"Failed to read JSON file {file_path}: {str(e)}")


def write_json_file(
    data: Dict[str, Any],
    file_path: Union[str, Path],
    indent: int = 2,
    ensure_ascii: bool = False
) -> None:
    """
    Write data to JSON file.
    
    Args:
        data: Data to write
        file_path: Path to output file
        indent: JSON indentation level
        ensure_ascii: If True, escape non-ASCII characters
        
    Raises:
        FileOperationError: If file cannot be written
    """
    try:
        path = validate_path(file_path, must_exist=False)
        
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
            
        logger.debug(f"Successfully wrote JSON file: {path}")
    except Exception as e:
        raise FileOperationError(f"Failed to write JSON file {file_path}: {str(e)}")


def generate_id(length: int = 8, prefix: str = "") -> str:
    """
    Generate a random identifier.
    
    Args:
        length: Length of random part
        prefix: Optional prefix
        
    Returns:
        Generated identifier
    """
    chars = string.ascii_letters + string.digits
    random_part = ''.join(random.choices(chars, k=length))
    return f"{prefix}{random_part}" if prefix else random_part


def calculate_md5(file_path: Union[str, Path], chunk_size: int = 8192) -> str:
    """
    Calculate MD5 hash of a file.
    
    Args:
        file_path: Path to file
        chunk_size: Size of chunks to read
        
    Returns:
        MD5 hash string
        
    Raises:
        FileOperationError: If file cannot be read
    """
    try:
        path = validate_path(file_path, must_exist=True)
        md5_hash = hashlib.md5()
        
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                md5_hash.update(chunk)
                
        return md5_hash.hexdigest()
    except Exception as e:
        raise FileOperationError(f"Failed to calculate MD5 for {file_path}: {str(e)}")


def format_timestamp(
    timestamp: Optional[datetime.datetime] = None,
    fmt: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """
    Format timestamp as string.
    
    Args:
        timestamp: Datetime object (uses current time if None)
        fmt: Format string
        
    Returns:
        Formatted timestamp string
    """
    if timestamp is None:
        timestamp = datetime.datetime.now()
    return timestamp.strftime(fmt)


def parse_timestamp(
    timestamp_str: str,
    fmt: str = "%Y-%m-%d %H:%M:%S"
) -> datetime.datetime:
    """
    Parse timestamp string to datetime object.
    
    Args:
        timestamp_str: Timestamp string
        fmt: Format string
        
    Returns:
        Parsed datetime object
        
    Raises:
        ValidationError: If timestamp cannot be parsed
    """
    try:
        return datetime.datetime.strptime(timestamp_str, fmt)
    except ValueError as e:
        raise ValidationError(f"Invalid timestamp '{timestamp_str}': {str(e)}")


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Exception, ...] = (Exception,)
):
    """
    Decorator for retrying functions on failure.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts in seconds
        backoff: Multiplier for delay after each failure
        exceptions: Tuple of exceptions to catch and retry on
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: "
                            f"{str(e)}. Retrying in {current_delay:.1f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}"
                        )
            
            raise last_exception
        return wrapper
    return decorator


@contextmanager
def timer(operation_name: str = "Operation"):
    """
    Context manager for timing operations.
    
    Args:
        operation_name: Name of the operation for logging
    """
    start_time = datetime.datetime.now()
    logger.info(f"{operation_name} started at {format_timestamp(start_time)}")
    
    try:
        yield
    finally:
        end_time = datetime.datetime.now()
        duration = end_time - start_time
        logger.info(
            f"{operation_name} completed at {format_timestamp(end_time)} "
            f"(duration: {duration.total_seconds():.2f}s)"
        )


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """
    Sanitize filename by removing or replacing invalid characters.
    
    Args:
        filename: Original filename
        replacement: Character to replace invalid characters with
        
    Returns:
        Sanitized filename
    """
    # Characters that are generally unsafe in filenames
    invalid_chars = '<>:"/\\|?*\'"'
    
    for char in invalid_chars:
        filename = filename.replace(char, replacement)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        filename = "unnamed_file"
    
    return filename


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    Get file size in bytes.
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in bytes
        
    Raises:
        FileOperationError: If file cannot be accessed
    """
    try:
        path = validate_path(file_path, must_exist=True)
        return path.stat().st_size
    except Exception as e:
        raise FileOperationError(f"Failed to get file size for {file_path}: {str(e)}")


def human_readable_size(size_bytes: int) -> str:
    """
    Convert size in bytes to human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human readable size string
    """
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    unit_index = 0
    
    while size_bytes >= 1024 and unit_index < len(units) - 1:
        size_bytes /= 1024.0
        unit_index += 1
    
    return f"{size_bytes:.2f} {units[unit_index]}"


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two dictionaries recursively.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if (key in result and isinstance(result[key], dict) 
                and isinstance(value, dict)):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks of specified size.
    
    Args:
        lst: Input list
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    if chunk_size <= 0:
        raise ValidationError("Chunk size must be positive")
    
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def is_valid_email(email: str) -> bool:
    """
    Basic email validation.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email appears valid, False otherwise
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def get_environment_variable(
    name: str,
    default: Optional[str] = None,
    required: bool = False
) -> Optional[str]:
    """
    Get environment variable with validation.
    
    Args:
        name: Environment variable name
        default: Default value if not found
        required: If True, raises error when variable is not set
        
    Returns:
        Environment variable value or default
        
    Raises:
        ValidationError: If required variable is not set
    """
    value = os.environ.get(name, default)
    
    if required and value is None:
        raise ValidationError(f"Required environment variable '{name}' is not set")
    
    return value


# Import time module for retry decorator
import time

# Initialize module
if __name__ == "__main__":
    logger.info("Project utilities module loaded")