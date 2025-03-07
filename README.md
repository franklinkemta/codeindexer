# CodeIndexer

[![PyPI version](https://badge.fury.io/py/codeindexer.svg)](https://badge.fury.io/py/codeindexer)

A lightweight CLI to generate LLM context-ready prompt file from a codebase.

## Why ?

Still doing some finger-hurting typing or copy-pasting just to update your LLM about code changes or set up context in new chats (the old way 😅, without copilots)?

I run this tool to generate a structured prompt with my project files, so all I have to do is copy, paste, and the model is ready to go! ⌛⏱️✨

## Installation ℹ️

```bash
pip install codeindexer

# Basic usage
codeindexer --index ./my_repo --format md index_file.md

# Filter by file extensions
codeindexer --index ./my_repo --only .py,.js,.md --format md index_file.md

# Skip specific directories or files
codeindexer --index ./my_repo --skip node_modules/,venv/,*.log --format md index_file.md

# Explicitly include files/paths (even if ignored by .gitignore)
codeindexer --index ./my_repo --include important.log,temp/config.json --format md index_file.md

# Add a custom prompt at the end
codeindexer --index ./my_repo --prompt "Analyze and suggest improvements." --format md index_file.md

# Disable .gitignore parsing
codeindexer --index ./my_repo --no-gitignore --format md index_file.md
````

Example Output prompt (index_file.md) 📋

```tree
# Repo: my_repo
# Folder structure:
my_repo/
├── src/
│   ├── main.py
│   ├── utils.py
├── tests/
│   ├── test_main.py
├── README.md
├── requirements.txt

# Files  
# my_repo/requirements.txt  
{contents of my_repo/requirements.txt}  

# my_repo/README.md  
{contents of my_repo/README.md}  

# my_repo/src/main.py  
{contents of my_repo/src/main.py}  

...  
________________________________________

Acknowledge the project's description and files, do no provide additional explanation, wait for instructions

```

## Options 🔧

- `--index`: Directory to index (required)
- `--only`: Comma-separated list of file extensions to include (e.g., .py,.js,.md)
- `--skip`: Comma-separated list of patterns to skip (e.g., node_modules/,venv/,*.log)
- `--include`: Comma-separated list of patterns to explicitly include even if in .gitignore
- `--format`: Output format (md, txt, json) - default is md
- `--prompt`: Custom prompt to add at the end of the index
- `--no-skip-env`: Include .env files (by default they are skipped)
- `--no-gitignore`: Disable automatic parsing of .gitignore files (enabled by default)


## Features ✨
- ✅ Generate a single file with your repo’s structure and files
- ✅ Automatically respects .gitignore rules 📋
- ✅ Filters files by extension and skips binaries 🔍
- ✅ Multiple output formats: Markdown, text, JSON 📝
- ✅ Add a custom prompt for LLM context 🤖
- ✅ Split output files into small parts

## Contributing 🤝
Contributions are welcome! Please check out our [Contributing Guide](CONTRIBUTING.md) for details on how to get started.

## License

MIT