"""Core functionality for indexing codebases."""

import os
import json
from pathlib import Path
from fnmatch import fnmatch
from typing import List, Dict, Optional, Any, Set

from .utils import build_directory_tree
from .gitignore_parser import parse_gitignore, is_binary_file


def create_index(
    index_dir: Path,
    output_path: Path,
    only_extensions: List[str] = None,
    skip_patterns: List[str] = None,
    include_patterns: List[str] = None,
    output_format: str = "md",
    prompt: str = "",
    use_gitignore: bool = True,
) -> None:
    """
    Create an index of the codebase at index_dir and save it to output_path.
    
    Args:
        index_dir: Path to the directory to index
        output_path: Path where the index will be saved
        only_extensions: List of file extensions to include
        skip_patterns: List of patterns to skip
        include_patterns: List of patterns to explicitly include even if in .gitignore
        output_format: Output format (md, txt, json)
        prompt: Custom prompt to add at the end of the index
        use_gitignore: Whether to use .gitignore patterns
    """
    # Normalize paths
    index_dir = index_dir.resolve()
    repo_name = index_dir.name
    
    # Initialize skip patterns
    final_skip_patterns = skip_patterns or []
    include_patterns = include_patterns or []
    
    # Add .gitignore patterns if enabled
    if use_gitignore:
        gitignore_patterns = parse_gitignore(index_dir)
        for pattern in gitignore_patterns:
            if not any(include_pattern in pattern for include_pattern in include_patterns):
                final_skip_patterns.append(pattern)
    
    # Collect files
    files = collect_files(
        index_dir, 
        only_extensions=only_extensions,
        skip_patterns=final_skip_patterns,
        include_patterns=include_patterns,
    )
    
    # Generate directory tree
    tree = build_directory_tree(index_dir, files)
    
    # Create index based on format
    if output_format == "json":
        create_json_index(index_dir, repo_name, files, tree, prompt, output_path)
    else:
        create_text_index(index_dir, repo_name, files, tree, prompt, output_path, is_markdown=(output_format == "md"))


def collect_files(
    index_dir: Path,
    only_extensions: Optional[List[str]] = None,
    skip_patterns: Optional[List[str]] = None,
    include_patterns: Optional[List[str]] = None,
) -> List[Path]:
    """
    Collect files to be indexed based on filters.
    
    Args:
        index_dir: Path to the directory to index
        only_extensions: List of file extensions to include
        skip_patterns: List of patterns to skip
        include_patterns: List of patterns to explicitly include
    
    Returns:
        List of file paths to be indexed
    """
    only_extensions = only_extensions or []
    skip_patterns = skip_patterns or []
    include_patterns = include_patterns or []
    
    files = []
    
    for root, dirs, filenames in os.walk(index_dir):
        # Process directories
        dirs_to_remove = []
        for d in dirs:
            dir_path = os.path.join(root, d)
            rel_dir_path = os.path.relpath(dir_path, index_dir)
            
            # Check if directory should be explicitly included
            should_include = False
            for include_pattern in include_patterns:
                if fnmatch(d, include_pattern) or fnmatch(rel_dir_path, include_pattern):
                    should_include = True
                    break
            
            # Skip directory based on patterns unless explicitly included
            if not should_include:
                for pattern in skip_patterns:
                    if (fnmatch(d, pattern) or 
                        fnmatch(dir_path, pattern) or 
                        fnmatch(rel_dir_path, pattern)):
                        dirs_to_remove.append(d)
                        break
        
        # Remove directories that match skip patterns
        for d in dirs_to_remove:
            dirs.remove(d)
        
        # Process files
        for filename in filenames:
            file_path = Path(os.path.join(root, filename))
            rel_path = file_path.relative_to(index_dir)
            rel_path_str = str(rel_path)
            
            # Check if file should be explicitly included
            should_include = False
            for include_pattern in include_patterns:
                if (fnmatch(filename, include_pattern) or 
                    fnmatch(rel_path_str, include_pattern)):
                    should_include = True
                    break
            
            # Skip files based on patterns unless explicitly included
            if not should_include:
                should_skip = False
                for pattern in skip_patterns:
                    if (fnmatch(filename, pattern) or 
                        fnmatch(rel_path_str, pattern) or 
                        fnmatch(str(file_path), pattern)):
                        should_skip = True
                        break
                
                if should_skip:
                    continue
                
                # Check file extension if only_extensions specified
                if only_extensions and not any(filename.endswith(ext) for ext in only_extensions):
                    continue
            
            # Add file to list
            files.append(file_path)
    
    return sorted(files)


def create_text_index(
    index_dir: Path,
    repo_name: str,
    files: List[Path],
    tree: str,
    prompt: str,
    output_path: Path,
    is_markdown: bool = True,
) -> None:
    """
    Create a text-based index (markdown or plain text).
    
    Args:
        index_dir: Path to the directory to index
        repo_name: Name of the repository
        files: List of files to index
        tree: Directory tree as string
        prompt: Custom prompt to add at the end
        output_path: Path where the index will be saved
        is_markdown: If True, use markdown formatting
    """
    heading_marker = "#" if is_markdown else ""
    separator = "```" if is_markdown else ""
    
    with open(output_path, "w", encoding="utf-8") as f:
        # Repository name
        f.write(f"{heading_marker} Repo: {repo_name}\n\n")
        
        # Directory structure
        f.write(f"{heading_marker} Folder structure:\n")
        f.write(tree)
        f.write("\n\n")
        
        # Files content
        f.write(f"{heading_marker} Files\n")
        
        for file_path in files:
            rel_path = file_path.relative_to(index_dir)
            f.write(f"\n{heading_marker} {repo_name}/{rel_path}\n")
            
            # Skip binary files
            if is_binary_file(file_path):
                f.write("[Binary file not shown]\n")
                continue
                
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as source_file:
                    content = source_file.read()
                
                # For markdown, wrap code content in code blocks
                if is_markdown and rel_path.suffix:
                    extension = rel_path.suffix.lstrip(".")
                    f.write(f"{separator}{extension}\n")
                    f.write(content)
                    f.write(f"\n{separator}\n")
                else:
                    f.write(content)
                    f.write("\n")
            except Exception as e:
                f.write(f"[Error reading file: {str(e)}]\n")
        
        # Add separator before prompt
        if prompt:
            f.write("\n" + "_" * 40 + "\n\n")
            f.write(prompt)


def create_json_index(
    index_dir: Path,
    repo_name: str,
    files: List[Path],
    tree: str,
    prompt: str,
    output_path: Path,
) -> None:
    """
    Create a JSON-based index.
    
    Args:
        index_dir: Path to the directory to index
        repo_name: Name of the repository
        files: List of files to index
        tree: Directory tree as string
        prompt: Custom prompt to add at the end
        output_path: Path where the index will be saved
    """
    index_data: Dict[str, Any] = {
        "repo_name": repo_name,
        "folder_structure": tree,
        "files": [],
        "prompt": prompt
    }
    
    for file_path in files:
        rel_path = str(file_path.relative_to(index_dir))
        
        # Skip binary files
        if is_binary_file(file_path):
            index_data["files"].append({
                "path": f"{repo_name}/{rel_path}",
                "content": "[Binary file not shown]"
            })
            continue
            
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as source_file:
                content = source_file.read()
            
            index_data["files"].append({
                "path": f"{repo_name}/{rel_path}",
                "content": content
            })
        except Exception as e:
            index_data["files"].append({
                "path": f"{repo_name}/{rel_path}",
                "error": str(e)
            })
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2)
