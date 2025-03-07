# CodeIndexer

A lightweight CLI tool for indexing codebases to provide context for LLMs.

## Installation

```bash
pip install codeindexer
```

## Usage

```bash
# Basic usage
codeindexer --index ./my_repo --format md index_file.md

# Include only specific file extensions
codeindexer --index ./my_repo --only .py,.js,.md --format md index_file.md

# Skip specific directories or files
codeindexer --index ./my_repo --skip node_modules/,venv/,*.log --format md index_file.md

# Explicitly include files/paths (even if they match .gitignore patterns)
codeindexer --index ./my_repo --include important.log,temp/config.json --format md index_file.md

# Add a custom prompt at the end of the index
codeindexer --index ./my_repo --prompt "Please analyze this codebase and suggest improvements." --format md index_file.md

# Disable .gitignore parsing
codeindexer --index ./my_repo --no-gitignore --format md index_file.md
```

## Options

- `--index`: Directory to index (required)
- `--only`: Comma-separated list of file extensions to include (e.g., .py,.js,.md)
- `--skip`: Comma-separated list of patterns to skip (e.g., node_modules/,venv/,*.log)
- `--include`: Comma-separated list of patterns to explicitly include even if in .gitignore
- `--format`: Output format (md, txt, json) - default is md
- `--prompt`: Custom prompt to add at the end of the index
- `--no-skip-env`: Include .env files (by default they are skipped)
- `--no-gitignore`: Disable automatic parsing of .gitignore files (enabled by default)

## Features

- Creates a single file with the content of all files in a repository
- Includes repository folder structure visualization
- Automatically respects .gitignore rules
- Detects and skips binary files
- Supports filtering by file extension
- Allows skipping specific directories or files
- Multiple output formats (markdown, text, json)
- Adds a custom prompt for LLM context

## License

MIT
