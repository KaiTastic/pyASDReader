# Contributing to pyASDReader

Thank you for your interest in contributing to pyASDReader! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Commit Messages](#commit-messages)
- [Pull Requests](#pull-requests)
- [Release Process](#release-process)

## Code of Conduct

Please be respectful and constructive in all interactions. We aim to maintain a welcoming and inclusive environment.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- Conda (recommended) or pip

### Setting Up Development Environment

1. **Fork and clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/pyASDReader.git
cd pyASDReader
```

2. **Create and activate conda environment** (recommended)

```bash
conda create -n pyasd python=3.10
conda activate pyasd
```

Or use venv:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install in development mode**

```bash
pip install -e ".[dev]"
```

This installs:
- The package in editable mode
- All development dependencies (pytest, black, flake8, etc.)

4. **Set up pre-commit hooks**

```bash
pre-commit install
pre-commit install --hook-type commit-msg
```

This enables automatic code formatting and validation before commits.

5. **Verify setup**

```bash
pytest tests/
```

All tests should pass.

## Development Workflow

### Branch Strategy

- **main**: Production-ready code, tagged releases only
- **dev**: Development branch, all features merged here first
- **feature/**: Feature branches (e.g., `feature/add-v9-support`)
- **fix/**: Bug fix branches (e.g., `fix/metadata-parsing`)

### Creating a Feature Branch

```bash
git checkout dev
git pull origin dev
git checkout -b feature/your-feature-name
```

### Making Changes

1. Write code following our [coding standards](#coding-standards)
2. Add tests for new functionality
3. Update documentation if needed
4. Run tests locally: `pytest tests/`
5. Commit with [conventional commits](#commit-messages)

### Syncing with Upstream

```bash
git fetch origin
git rebase origin/dev
```

## Coding Standards

### Python Style Guide

- **PEP 8** compliance (enforced by flake8)
- **Black** for code formatting (line length: 120)
- **isort** for import sorting

### Code Quality Tools

All are configured in `pyproject.toml` and run automatically via pre-commit:

```bash
# Manual formatting
black src/ tests/
isort src/ tests/

# Manual linting
flake8 src/ tests/

# Run all pre-commit checks
pre-commit run --all-files
```

### Documentation

- Docstrings for all public functions/classes (Google style)
- Type hints where appropriate
- Comments for complex logic
- Update README.md for user-facing changes

### Example Code Style

```python
def parse_metadata(data: bytes, offset: int = 0) -> tuple[dict, int]:
    """
    Parse ASD file metadata from binary data.

    Args:
        data: Binary data containing ASD file
        offset: Starting position in data (default: 0)

    Returns:
        Tuple of (metadata_dict, next_offset)

    Raises:
        ValueError: If data format is invalid
    """
    # Implementation
    pass
```

## Testing

### Running Tests

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/test_asd_file_reader.py

# With coverage report
pytest tests/ --cov=pyASDReader --cov-report=html
```

### Writing Tests

- Place tests in `tests/` directory
- Use descriptive test names: `test_<feature>_<scenario>_<expected_result>`
- Use pytest fixtures for common setup
- Aim for high coverage (target: >80%)

Example:

```python
def test_parse_version6_file_returns_correct_metadata():
    """Test that v6 files are parsed correctly."""
    asd_file = ASDFile("tests/sample_data/v6sample/sample.asd")
    assert asd_file.asdFileVersion.value == 6
    assert asd_file.metadata.instrumentType is not None
```

### Test Data

- Sample ASD files are in `tests/sample_data/`
- Do not commit large test files (>1MB)
- Document test data sources

## Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
type(scope): Description

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes
- `build`: Build system changes

### Examples

```
feat: Add support for ASD file version 9

fix: Correct GPS coordinate parsing for negative values

docs: Update README with v9 file format notes

chore(deps): Update numpy to 1.26.0

test: Add comprehensive tests for metadata parsing
```

### Validation

Commit messages are validated automatically by pre-commit hooks. Invalid messages will be rejected.

## Pull Requests

### Before Submitting

1. Ensure all tests pass: `pytest tests/`
2. Check code quality: `pre-commit run --all-files`
3. Update CHANGELOG.md (add to [Unreleased] section)
4. Rebase on latest dev: `git rebase origin/dev`

### PR Template

When creating a PR, include:

**Title**: Follow conventional commit format (e.g., `feat: Add version 9 support`)

**Description**:
```markdown
## Summary
Brief description of changes

## Changes
- Bullet list of specific changes
- What was added/fixed/changed

## Testing
How the changes were tested

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] All tests passing
- [ ] Pre-commit hooks passing
```

### Review Process

1. Automated checks (CI/CD) must pass
2. At least one maintainer review required
3. Address review comments
4. Maintainer will merge when approved

### Merge Strategy

- **Squash and merge** for feature PRs (keeps history clean)
- **Merge commit** for release PRs (preserves history)

## Release Process

Releases are managed by maintainers using our automated release script.

### For Maintainers

1. **Ensure all changes are in dev branch**

2. **Run automated release script**

```bash
git checkout dev
bash scripts/release.sh <version>

# Examples:
bash scripts/release.sh patch  # 1.2.3 -> 1.2.4
bash scripts/release.sh minor  # 1.2.3 -> 1.3.0
bash scripts/release.sh major  # 1.2.3 -> 2.0.0
```

3. **Script will automatically**:
   - Validate branch and working directory
   - Update CHANGELOG.md
   - Merge dev -> main
   - Create version tag
   - Push to GitHub
   - Trigger CI/CD for PyPI release

4. **Monitor the release**:
   - GitHub Actions: https://github.com/KaiTastic/pyASDReader/actions
   - PyPI: https://pypi.org/project/pyASDReader/

See [VERSION_MANAGEMENT.md](VERSION_MANAGEMENT.md) for detailed release documentation.

## Questions?

- **Issues**: [GitHub Issues](https://github.com/KaiTastic/pyASDReader/issues)
- **Discussions**: [GitHub Discussions](https://github.com/KaiTastic/pyASDReader/discussions)
- **Email**: caokai_cgs@163.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
