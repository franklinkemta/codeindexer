"""Utility functions for the CodeIndexer."""

from pathlib import Path
from typing import List, Dict


def build_directory_tree(base_dir: Path, files: List[Path]) -> str:
    """
    Build a directory tree visualization of the repository using standard tree symbols (├──, └──, │).
    
    Args:
        base_dir: The base directory of the repository
        files: List of files in the repository
    
    Returns:
        String representation of the directory tree
    """
    base_dir = base_dir.resolve()
    hierarchy: Dict = {}
    for file_path in files:
        rel_path = file_path.relative_to(base_dir)
        parts = rel_path.parts
        current = hierarchy
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                current.setdefault("__files__", []).append(part)
            else:
                if part not in current:
                    current[part] = {}
                current = current[part]
    lines = [f"{base_dir.name}/"]
    _build_tree_lines_standard(hierarchy, lines, prefix="", is_last=True)
    return "\n".join(lines)

def _build_tree_lines_standard(
    node: Dict,
    lines: List[str],
    prefix: str = "",
    is_last: bool = True,
):
    """
    Recursively build lines for the directory tree using standard tree symbols.
    
    Args:
        node: Current node in the hierarchy
        lines: List to append lines to
        prefix: Prefix for the current line (for indentation and vertical lines)
        is_last: Whether this is the last entry in the current directory
    """
    dirs = sorted([k for k in node.keys() if k != "__files__"])
    files = sorted(node.get("__files__", []))
    entries = dirs + files
    for idx, name in enumerate(entries):
        connector = "└── " if idx == len(entries) - 1 else "├── "
        is_dir = name in node
        line = f"{prefix}{connector}{name}/" if is_dir else f"{prefix}{connector}{name}"
        lines.append(line)
        if is_dir:
            # If last entry, don't add vertical line for children
            child_prefix = prefix + ("    " if idx == len(entries) - 1 else "│   ")
            _build_tree_lines_standard(node[name], lines, child_prefix, is_last=(idx == len(entries) - 1))