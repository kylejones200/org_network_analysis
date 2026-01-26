# Contributing to OrgNet Three E's

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

### Prerequisites
- Python 3.12 or higher
- Ubuntu (recommended)
- Docker and Docker Compose (for full stack)
- Git

### Quick Start

1. **Clone the repository**
```bash
git clone <repository-url>
cd orgnet
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Copy environment configuration**
```bash
cp env.example .env
# Edit .env with your settings
```

5. **Initialize database**
```bash
python -c "from app.database import init_db; init_db('sqlite:///orgnet.db')"
```

6. **Run tests**
```bash
pytest tests/ -v
```

7. **Start development server**
```bash
python -m app.app
```

## Running with Docker

```bash
docker-compose up
```

The API will be available at `http://localhost:5000`

## Development Guidelines

### Code Style
- Follow PEP 8
- Use Black for formatting: `black .`
- Run linting: `flake8 .`
- Type hints are encouraged

### Testing
- Write tests for all new features
- Maintain test coverage above 70%
- Run tests before submitting PR: `pytest tests/`
- Test fixtures are in `tests/conftest.py`

### Commits
- Use clear, descriptive commit messages
- Reference issues in commits: `Fix #123: Description`
- Keep commits focused and atomic

### Pull Requests
1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Write/update tests
4. Update documentation if needed
5. Run tests: `pytest tests/`
6. Push and create PR

## Project Structure

```
orgnet/
├── app/
│   ├── database/          # Layer 1: Database models
│   ├── data_access/       # Layer 2: Repository pattern
│   ├── business_logic/    # Layer 3: Core algorithms
│   ├── app.py            # Layer 4: Flask API
│   ├── config.py         # Configuration
│   ├── validation.py     # Request validation
│   └── *.py              # Utility modules
├── tests/            # Test suite
└── *.py              # Root-level scripts
```

## What to Contribute

### High Priority
- Bug fixes
- Test coverage improvements
- Documentation improvements
- Performance optimizations (with benchmarks)

### Medium Priority
- New metrics based on research
- API improvements
- Better error messages
- Example applications

### Please Avoid
- Adding features without discussion (open an issue first)
- Breaking changes to public API
- Removing tests
- Adding dependencies without justification

## Questions?

- Open an issue for bugs or feature requests
- Check existing issues before creating new ones
- Be respectful and constructive

Thank you for contributing!
