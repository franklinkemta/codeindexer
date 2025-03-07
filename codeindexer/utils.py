"""Utility functions for the CodeIndexer."""

from pathlib import Path
from typing import List, Dict


def build_directory_tree(base_dir: Path, files: List[Path]) -> str:
    """
    Build a directory tree visualization of the repository.
    
    Args:
        base_dir: The base directory of the repository
        files: List of files in the repository
    
    Returns:
        String representation of the directory tree
    """
    base_dir = base_dir.resolve()
    
    # Build a hierarchy from files
    hierarchy: Dict = {}
    
    for file_path in files:
        rel_path = file_path.relative_to(base_dir)
        parts = rel_path.parts
        
        current = hierarchy
        for i, part in enumerate(parts):
            if i == len(parts) - 1:  # Last part (file)
                current.setdefault("__files__", []).append(part)
            else:  # Directory
                if part not in current:
                    current[part] = {}
                current = current[part]
    
    # Convert hierarchy to string
    lines = []
    _build_tree_lines(hierarchy, "", "", lines, is_root=True, base_name=base_dir.name)
    
    return "\n".join(lines)


def _build_tree_lines(
    node: Dict,
    prefix: str,
    child_prefix: str,
    lines: List[str],
    is_root: bool = False,
    base_name: str = "",
) -> None:
    """
    Recursively build lines for the directory tree.
    
    Args:
        node: Current node in the hierarchy
        prefix: Prefix for the current line
        child_prefix: Prefix for child lines
        lines: List to append lines to
        is_root: Whether this is the root node
        base_name: Name of the base directory (for root)
    """
    if is_root:
        lines.append(f"|_ {base_name}/")
        new_prefix = child_prefix + "          |"
    else:
        new_prefix = child_prefix
    
    # Process directories
    dirs = sorted([k for k in node.keys() if k != "__files__"])
    for i, dir_name in enumerate(dirs):
        is_last_dir = i == len(dirs) - 1 and not node.get("__files__")
        
        if is_root:
            dir_line = f"{new_prefix}_"
        else:
            dir_line = f"{prefix}_"
        
        lines.append(f"{dir_line}{dir_name}/")
        
        if is_last_dir:
            _build_tree_lines(
                node[dir_name],
                f"{child_prefix}                   ",
                f"{child_prefix}                   ",
                lines,
            )
        else:
            _build_tree_lines(
                node[dir_name],
                f"{child_prefix}                   |",
                f"{child_prefix}                   |",
                lines,
            )
    
    # Process files
    files = sorted(node.get("__files__", []))
    for i, file_name in enumerate(files):
        if is_root:
            file_line = f"{new_prefix}_"
        else:
            file_line = f"{prefix}_"
        
        lines.append(f"{file_line}{file_name}")