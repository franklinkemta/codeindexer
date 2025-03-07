"""Core functionality for indexing codebases."""

import os
import json
from pathlib import Path
from fnmatch import fnmatch
from typing import List, Dict, Optional, Any, Set, Callable

from .utils import build_directory_tree
from .gitignore_parser import parse_gitignore, is_binary_file

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
                    # Normalize pattern for directory matching
                    if pattern.endswith('/'):
                        dir_pattern = pattern
                        path_pattern = pattern[:-1]
                    else:
                        dir_pattern = pattern + '/'
                        path_pattern = pattern
                    
                    # Match against directory name, absolute path, or relative path
                    if (fnmatch(d, pattern) or 
                        fnmatch(d, path_pattern) or
                        fnmatch(d + '/', dir_pattern) or 
                        fnmatch(dir_path, pattern) or 
                        fnmatch(rel_dir_path, pattern) or
                        fnmatch(rel_dir_path + '/', dir_pattern)):
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

def create_index(
    index_dir: Path,
    output_path: Path,
    only_extensions: List[str] = None,
    skip_patterns: List[str] = None,
    include_patterns: List[str] = None,
    output_format: str = "md",
    prompt: str = "",
    use_gitignore: bool = True,
    split_max_lines: Optional[int] = None,
    progress_callback: Optional[Callable] = None,
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
        split_max_lines: Maximum lines per file when splitting output
        progress_callback: Callback function for progress updates
    """
    # Report progress
    if progress_callback:
        progress_callback("Initializing", 0, 100)
    
    # Normalize paths
    index_dir = index_dir.resolve()
    repo_name = index_dir.name
    
    # Initialize skip patterns
    final_skip_patterns = skip_patterns or []
    include_patterns = include_patterns or []
    
    # Add .gitignore patterns if enabled
    if use_gitignore:
        if progress_callback:
            progress_callback("Parsing .gitignore", 5, 100)
        
        gitignore_patterns = parse_gitignore(index_dir)
        for pattern in gitignore_patterns:
            if not any(include_pattern in pattern for include_pattern in include_patterns):
                final_skip_patterns.append(pattern)
    
    # Collect files
    if progress_callback:
        progress_callback("Collecting files", 10, 100)
    
    files = collect_files(
        index_dir, 
        only_extensions=only_extensions,
        skip_patterns=final_skip_patterns,
        include_patterns=include_patterns,
    )
    
    # Generate directory tree
    if progress_callback:
        progress_callback("Building directory tree", 20, 100)
    
    tree = build_directory_tree(index_dir, files)
    
    # Create index based on format
    if progress_callback:
        progress_callback("Creating index", 30, 100)
    
    if output_format == "json":
        create_json_index(
            index_dir,
            repo_name,
            files,
            tree,
            prompt,
            output_path,
            split_max_lines=split_max_lines,
            progress_callback=progress_callback
        )
    else:
        create_text_index(
            index_dir,
            repo_name,
            files,
            tree,
            prompt,
            output_path,
            is_markdown=(output_format == "md"),
            split_max_lines=split_max_lines,
            progress_callback=progress_callback
        )


def create_text_index(
    index_dir: Path,
    repo_name: str,
    files: List[Path],
    tree: str,
    prompt: str,
    output_path: Path,
    is_markdown: bool = True,
    split_max_lines: Optional[int] = None,
    progress_callback: Optional[Callable] = None,
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
        split_max_lines: Maximum lines per file when splitting output
        progress_callback: Callback function for progress updates
    """
    heading_marker = "#" if is_markdown else ""
    separator = "```" if is_markdown else ""
    comment_marker = "<!--" if is_markdown else "!-"
    comment_end = "-->" if is_markdown else "-!"
    file_extension = output_path.suffix
    
    # If splitting, create directory for chunks
    if split_max_lines:
        split_dir = output_path.parent / output_path.stem
        split_dir.mkdir(exist_ok=True)
        content_lines = []
        
        # Add intro content
        content_lines.append(f"{heading_marker} Repo: {repo_name}\n")
        content_lines.append(f"{heading_marker} Folder structure:\n")
        content_lines.extend(tree.split('\n'))
        content_lines.append("\n")
        content_lines.append(f"{heading_marker} Files\n")
        
        # Process files
        total_files = len(files)
        for index, file_path in enumerate(files):
            # Update progress
            if progress_callback:
                progress_percentage = 30 + (60 * ((index + 1) / total_files))
                progress_callback(
                    "Processing files", 
                    progress_percentage, 
                    100, 
                    f"Processing {index+1}/{total_files}: {file_path.name}"
                )
            
            rel_path = file_path.relative_to(index_dir)
            content_lines.append(f"\n{heading_marker} {repo_name}/{rel_path}\n")
            
            # Skip binary files
            if is_binary_file(file_path):
                content_lines.append("[Binary file not shown]\n")
                continue
                
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as source_file:
                    file_content = source_file.read()
                
                # For markdown, wrap code content in code blocks
                if is_markdown and rel_path.suffix:
                    extension = rel_path.suffix.lstrip(".")
                    content_lines.append(f"{separator}{extension}")
                    content_lines.extend(file_content.split('\n'))
                    content_lines.append(f"{separator}\n")
                else:
                    content_lines.extend(file_content.split('\n'))
                    content_lines.append("\n")
            except Exception as e:
                content_lines.append(f"[Error reading file: {str(e)}]\n")
        
        # Add separator before prompt
        if prompt:
            content_lines.append("\n" + "_" * 40 + "\n")
            content_lines.extend(prompt.split('\n'))
        
        # Split content into chunks
        chunk_index = 0
        current_chunk = []
        for line in content_lines:
            current_chunk.append(line)
            
            # When chunk reaches max size, write to file
            if len(current_chunk) >= split_max_lines:
                chunk_path = split_dir / f"{output_path.stem}.{chunk_index}{file_extension}"
                
                with open(chunk_path, "w", encoding="utf-8") as f:
                    if chunk_index == 0:
                        f.write(f"{comment_marker} First part {comment_end}\n\n")
                    else:
                        f.write(f"{comment_marker} Part {chunk_index} {comment_end}\n\n")
                    
                    f.write('\n'.join(current_chunk))
                    f.write(f"\n\n{comment_marker} Partial part, next part follows... {comment_end}\n")
                
                # Reset for next chunk
                current_chunk = []
                chunk_index += 1
        
        # Write final chunk if there's content left
        if current_chunk:
            chunk_path = split_dir / f"{output_path.stem}.{chunk_index}{file_extension}"
            
            with open(chunk_path, "w", encoding="utf-8") as f:
                if chunk_index == 0:
                    f.write(f"{comment_marker} First and final part {comment_end}\n\n")
                else:
                    f.write(f"{comment_marker} Final part (part {chunk_index}) {comment_end}\n\n")
                
                f.write('\n'.join(current_chunk))
                f.write(f"\n\n{comment_marker} Final part {comment_end}\n")
        
        # Create a summary file at the original output path
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"{heading_marker} Index for {repo_name}\n\n")
            f.write(f"This index has been split into {chunk_index + 1} parts.\n\n")
            for i in range(chunk_index + 1):
                f.write(f"- Part {i}: {output_path.stem}/{output_path.stem}.{i}{file_extension}\n")
    
    else:
        # No splitting - write directly to output file
        with open(output_path, "w", encoding="utf-8") as f:
            # Repository name
            f.write(f"{heading_marker} Repo: {repo_name}\n\n")
            
            # Directory structure
            f.write(f"{heading_marker} Folder structure:\n")
            f.write(tree)
            f.write("\n\n")
            
            # Files content
            f.write(f"{heading_marker} Files\n")
            
            total_files = len(files)
            for index, file_path in enumerate(files):
                # Update progress
                if progress_callback:
                    progress_percentage = 30 + (60 * ((index + 1) / total_files))
                    progress_callback(
                        "Processing files", 
                        progress_percentage, 
                        100, 
                        f"Processing {index+1}/{total_files}: {file_path.name}"
                    )
                
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
    
    # Final progress update
    if progress_callback:
        progress_callback("Completed", 100, 100, "Indexed!")


def create_json_index(
    index_dir: Path,
    repo_name: str,
    files: List[Path],
    tree: str,
    prompt: str,
    output_path: Path,
    split_max_lines: Optional[int] = None,
    progress_callback: Optional[Callable] = None,
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
        split_max_lines: Maximum lines per file when splitting output
        progress_callback: Callback function for progress updates
    """
    index_data: Dict[str, Any] = {
        "repo_name": repo_name,
        "folder_structure": tree,
        "files": [],
        "prompt": prompt
    }
    
    total_files = len(files)
    for index, file_path in enumerate(files):
        # Update progress
        if progress_callback:
            progress_percentage = 30 + (60 * ((index + 1) / total_files))
            progress_callback(
                "Processing files", 
                progress_percentage, 
                100, 
                f"Processing {index+1}/{total_files}: {file_path.name}"
            )
        
        rel_path = file_path.relative_to(index_dir)
        rel_path_str = str(rel_path)
        
        # Skip binary files
        if is_binary_file(file_path):
            index_data["files"].append({
                "path": f"{repo_name}/{rel_path_str}",
                "content": "[Binary file not shown]"
            })
            continue
            
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as source_file:
                content = source_file.read()
            
            index_data["files"].append({
                "path": f"{repo_name}/{rel_path_str}",
                "content": content
            })
        except Exception as e:
            index_data["files"].append({
                "path": f"{repo_name}/{rel_path_str}",
                "error": str(e)
            })
    
    # Handle splitting for JSON format
    if split_max_lines:
        split_dir = output_path.parent / output_path.stem
        split_dir.mkdir(exist_ok=True)
        
        # Convert to string to count lines
        full_json = json.dumps(index_data, indent=2)
        json_lines = full_json.split('\n')
        
        # Calculate number of chunks needed
        num_chunks = (len(json_lines) + split_max_lines - 1) // split_max_lines
        
        # Create a summary file at the original path
        summary = {
            "repo_name": repo_name,
            "split_index": True,
            "num_parts": num_chunks,
            "parts": [f"{output_path.stem}/{output_path.stem}.{i}.json" for i in range(num_chunks)]
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        
        # Split json into chunks
        for i in range(num_chunks):
            start_line = i * split_max_lines
            end_line = min((i + 1) * split_max_lines, len(json_lines))
            
            # For first and last chunks, we need special handling
            if i == 0:
                chunk_data = {
                    "part": i,
                    "total_parts": num_chunks,
                    "is_first": True,
                    "is_last": (num_chunks == 1),
                    "repo_name": repo_name,
                    "folder_structure": tree,
                    "files": index_data["files"][:len(index_data["files"]) // num_chunks]
                }
            elif i == num_chunks - 1:
                chunk_data = {
                    "part": i,
                    "total_parts": num_chunks,
                    "is_first": False,
                    "is_last": True,
                    "files": index_data["files"][i * len(index_data["files"]) // num_chunks:],
                    "prompt": prompt
                }
            else:
                start_idx = i * len(index_data["files"]) // num_chunks
                end_idx = (i + 1) * len(index_data["files"]) // num_chunks
                
                chunk_data = {
                    "part": i,
                    "total_parts": num_chunks,
                    "is_first": False,
                    "is_last": False,
                    "files": index_data["files"][start_idx:end_idx]
                }
            
            # Write chunk to file
            chunk_path = split_dir / f"{output_path.stem}.{i}.json"
            with open(chunk_path, "w", encoding="utf-8") as f:
                json.dump(chunk_data, f, indent=2)
    else:
        # No splitting - write directly to output file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=2)
    
    # Final progress update
    if progress_callback:
        progress_callback("Completed", 100, 100, "Indexed!")
