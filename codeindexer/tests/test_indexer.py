"""Tests for the indexer module."""

import os
import tempfile
import pytest
from pathlib import Path

from codeindexer.indexer import collect_files, create_index


def create_test_repo():
    """Create a temporary test repository structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_dir = Path(temp_dir) / "test_repo"
        repo_dir.mkdir()
        
        # Create files
        (repo_dir / "README.md").write_text("# Test Repository")
        (repo_dir / ".env").write_text("SECRET=123")
        
        # Create src directory with files
        src_dir = repo_dir / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("print('Hello, world!')")
        (src_dir / "utils.py").write_text("def add(a, b): return a + b")
        
        # Create tests directory with files
        tests_dir = repo_dir / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_main.py").write_text("# Test file")
        
        # Create node_modules directory
        node_modules = repo_dir / "node_modules"
        node_modules.mkdir()
        (node_modules / "some_lib.js").write_text("// Some JS code")
        
        return repo_dir


def test_collect_files():
    """Test collecting files with various filters."""
    repo_dir = create_test_repo()
    
    # Test collecting all files
    all_files = collect_files(repo_dir)
    # Should include 5 files (.env, README.md, main.py, utils.py, test_main.py)
    # but not node_modules
    assert len(all_files) == 5
    
    # Test with only extensions
    py_files = collect_files(repo_dir, only_extensions=[".py"])
    assert len(py_files) == 3
    assert all(f.suffix == ".py" for f in py_files)
    
    # Test with skip patterns
    no_env_files = collect_files(repo_dir, skip_patterns=["*.env"])
    assert len(no_env_files) == 4
    assert not any(f.name == ".env" for f in no_env_files)
    
    # Test with skip directories
    no_tests_files = collect_files(repo_dir, skip_patterns=["tests/"])
    assert len(no_tests_files) == 4
    assert not any("tests" in str(f) for f in no_tests_files)


def test_create_index():
    """Test creating an index file."""
    repo_dir = create_test_repo()
    
    # Test creating a markdown index
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as md_file:
        md_path = Path(md_file.name)
    
    try:
        create_index(
            index_dir=repo_dir,
            output_path=md_path,
            only_extensions=[".py", ".md"],
            skip_patterns=["node_modules/"],
            output_format="md",
            prompt="Please analyze this code."
        )
        
        content = md_path.read_text()
        assert f"# Repo: {repo_dir.name}" in content
        assert "# Folder structure:" in content
        assert "```py" in content
        assert "Please analyze this code." in content
    finally:
        os.unlink(md_path)
    
    # Test creating a JSON index
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as json_file:
        json_path = Path(json_file.name)
    
    try:
        create_index(
            index_dir=repo_dir,
            output_path=json_path,
            only_extensions=[".py"],
            skip_patterns=["tests/"],
            output_format="json",
            prompt="Please analyze this code."
        )
        
        import json
        with open(json_path) as f:
            data = json.load(f)
        
        assert data["repo_name"] == repo_dir.name
        assert len(data["files"]) == 2  # main.py and utils.py
        assert data["prompt"] == "Please analyze this code."
    finally:
        os.unlink(json_path)


def test_create_index_with_progress():
    """Test creating an index file with progress callback."""
    repo_dir = create_test_repo()
    
    # Test creating a markdown index with progress
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as md_file:
        md_path = Path(md_file.name)
    
    try:
        progress_updates = []
        
        def mock_progress_callback(status, current, total, message=None):
            progress_updates.append({
                "status": status,
                "current": current,
                "total": total,
                "message": message
            })
        
        create_index(
            index_dir=repo_dir,
            output_path=md_path,
            only_extensions=[".py", ".md"],
            skip_patterns=["node_modules/"],
            output_format="md",
            prompt="Please analyze this code.",
            progress_callback=mock_progress_callback
        )
        
        # Check that progress was reported
        assert len(progress_updates) > 0
        assert progress_updates[0]["status"] == "Initializing"
        assert progress_updates[-1]["status"] == "Completed"
        assert progress_updates[-1]["current"] == 100
        
        content = md_path.read_text()
        assert f"# Repo: {repo_dir.name}" in content
    finally:
        os.unlink(md_path)


def test_create_index_with_split():
    """Test creating an index file with file splitting."""
    repo_dir = create_test_repo()
    
    # Test creating a markdown index with split
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as md_file:
        md_path = Path(md_file.name)
    
    try:
        split_dir = md_path.parent / f"{md_path.stem}_files"
        
        create_index(
            index_dir=repo_dir,
            output_path=md_path,
            only_extensions=[".py", ".md"],
            skip_patterns=["node_modules/"],
            output_format="md",
            prompt="Please analyze this code.",
            split=True
        )
        
        # Check that split dir was created
        assert split_dir.exists()
        assert split_dir.is_dir()
        
        # Check that files were split
        assert (split_dir / "README.md").exists()
        assert (split_dir / "src" / "main.py").exists()
        assert (split_dir / "src" / "utils.py").exists()
        
        # Check content of main index
        content = md_path.read_text()
        assert f"# Repo: {repo_dir.name}" in content
        assert f"[See file: {md_path.stem}_files/README.md]" in content
        assert f"[See file: {md_path.stem}_files/src/main.py]" in content
    finally:
        os.unlink(md_path)
        # Clean up split directory
        if split_dir.exists():
            import shutil
            shutil.rmtree(split_dir)
