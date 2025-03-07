"""Parser for .gitignore files."""

from pathlib import Path
from typing import List


def parse_gitignore(repo_dir: Path) -> List[str]:
    """
    Parse .gitignore files and return a list of patterns to skip.
    
    Args:
        repo_dir: Repository root directory
    
    Returns:
        List of patterns to skip
    """
    gitignore_path = repo_dir / ".gitignore"
    patterns = set()
    
    if gitignore_path.exists():
        with open(gitignore_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                    
                # Handle negation (!) patterns
                if line.startswith('!'):
                    # We're keeping these items explicitly, but for now we'll just skip them
                    continue
                
                # Remove trailing slashes for directories and add them to patterns
                if line.endswith('/'):
                    patterns.add(line[:-1] + '**')
                    patterns.add(line)
                else:
                    patterns.add(line)
                    # Also add pattern with trailing slash to match directories
                    patterns.add(line + '/')
    
    # Add common patterns that should always be ignored
    common_patterns = [
        "__pycache__/",
        "*.py[cod]",
        "*$py.class",
        "*.so",
        ".Python",
        "build/",
        "develop-eggs/",
        "dist/",
        "downloads/",
        "eggs/",
        ".eggs/",
        "lib/",
        "lib64/",
        "parts/",
        "sdist/",
        "var/",
        "wheels/",
        "*.egg-info/",
        ".installed.cfg",
        "*.egg",
        ".env",
        ".venv",
        "env/",
        "venv/",
        ".venv/",
        "ENV/",
        "env.bak/",
        "venv.bak/",
        ".idea/",
        ".vscode/",
        "*.swp",
        "*.swo",
        ".DS_Store",
        ".coverage",
        "htmlcov/",
        ".pytest_cache/",
        ".git/",
    ]
    
    for pattern in common_patterns:
        patterns.add(pattern)
    
    return list(patterns)


def is_binary_file(file_path: Path) -> bool:
    """
    Check if a file is binary.
    
    Args:
        file_path: Path to the file
    
    Returns:
        True if the file is binary, False otherwise
    """
    # Common binary file extensions
    binary_extensions = {
        '.pyc', '.pyd', '.pyo', '.so', '.dll', '.exe', '.bin', '.dat', 
        '.db', '.sqlite', '.sqlite3', '.jpg', '.jpeg', '.png', '.gif', 
        '.bmp', '.ico', '.pdf', '.doc', '.docx', '.ppt', '.pptx', 
        '.xls', '.xlsx', '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar',
        '.mp3', '.mp4', '.avi', '.mov', '.flv', '.wmv', '.wma', '.aac',
        '.o', '.a', '.lib', '.dylib', '.class', '.jar', '.war', '.ear'
    }
    
    # Check extension first (faster)
    if file_path.suffix.lower() in binary_extensions:
        return True
    
    # If extension check doesn't catch it, check file content
    try:
        # Read the first 8192 bytes to check for binary content
        chunk_size = 8192
        with open(file_path, 'rb') as f:
            chunk = f.read(chunk_size)
            
        # Check for null bytes which typically indicate binary content
        if b'\x00' in chunk:
            return True
            
        # Try to decode as text to see if it raises an exception
        try:
            chunk.decode('utf-8')
            return False
        except UnicodeDecodeError:
            return True
    except Exception:
        # If we can't open or process the file, assume it's binary to be safe
        return True
