# Contributing to CodeIndexer

First off, thank you for considering contributing to CodeIndexer! It's people like you that make this tool better for everyone.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/franklinkemta/codeindexer.git`
3. Create a virtual environment: `python -m venv .venv`
4. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Unix/MacOS: `source .venv/bin/activate`
5. Install dependencies: `pip install -e ".[dev]"`

## Development Process

1. Create a new branch for your feature: `git checkout -b feature-name`
2. Make your changes
3. Run tests: `pytest`
4. Format your code: `black .`
5. Lint your code: `flake8`
6. Commit your changes: `git commit -m "Add some feature"`
7. Push to your fork: `git push origin feature-name`
8. Submit a pull request

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update the version number in pyproject.toml if applicable
3. The PR will be merged once it has been reviewed and approved

## Code of Conduct

Please be respectful and considerate of others when contributing to this project.

## Questions?

Feel free to open an issue if you have any questions or need help.