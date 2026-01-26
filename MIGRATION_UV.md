# Migration to uv

This project has been migrated from pip/requirements.txt to [uv](https://github.com/astral-sh/uv), a fast Python package manager and resolver.

## What Changed

- **Package Manager**: Switched from `pip` to `uv`
- **Dependency Management**: Moved from `requirements.txt` to `pyproject.toml` with `uv.lock`
- **Linting**: Replaced `flake8` and `black` with `ruff` (faster, unified tool)
- **Virtual Environment**: Automatically managed by `uv` (no manual `venv` creation needed)

## Command Migration Guide

### Installation

**Old:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**New:**
```bash
uv sync
```

### Running Commands

**Old:**
```bash
python app.py
pytest tests/
black .
flake8 .
mypy app
```

**New:**
```bash
uv run python -m app.app
uv run pytest tests/
uv run ruff format .
uv run ruff check .
uv run mypy app
```

### Development Workflow

**Old:**
```bash
# Install dev dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Format code
black .

# Lint code
flake8 .
```

**New:**
```bash
# Install all dependencies (including dev)
uv sync

# Run tests
uv run pytest tests/ -v

# Format code
uv run ruff format .

# Lint code
uv run ruff check .
```

### Building and Publishing

**Old:**
```bash
python -m build
twine check dist/*
twine upload dist/*
```

**New:**
```bash
uv run python -m build
uv run twine check dist/*
uv run twine upload dist/*
```

### Adding Dependencies

**Old:**
```bash
pip install some-package
# Manually add to requirements.txt
```

**New:**
```bash
uv add some-package
# Automatically updates pyproject.toml and uv.lock
```

### Adding Dev Dependencies

**Old:**
```bash
pip install --dev some-dev-package
# Manually add to requirements.txt
```

**New:**
```bash
uv add --dev some-dev-package
# Automatically updates pyproject.toml and uv.lock
```

## Benefits

1. **Faster**: uv is 10-100x faster than pip
2. **Deterministic**: `uv.lock` ensures reproducible builds
3. **Unified**: Single tool for package management, linting, and formatting
4. **Modern**: Uses PEP 621 standard for project metadata
5. **Automatic**: No need to manually manage virtual environments

## Requirements.txt (Legacy)

The `requirements.txt` file is kept for reference but is **no longer the source of truth**. 
All dependencies are now managed in `pyproject.toml` and locked in `uv.lock`.

If you need to use `requirements.txt` for compatibility, you can generate it:
```bash
uv pip compile pyproject.toml -o requirements.txt
```

However, we recommend using `uv sync` directly.

## Troubleshooting

### uv not found
Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Lock file out of sync
Regenerate the lock file:
```bash
uv lock
```

### Virtual environment issues
Remove `.venv` and re-sync:
```bash
rm -rf .venv
uv sync
```

## Further Reading

- [uv Documentation](https://github.com/astral-sh/uv)
- [PEP 621 - Project Metadata](https://peps.python.org/pep-0621/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)

