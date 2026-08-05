# Contributing to PassClash

First off, thank you for taking the time to contribute! Contributions from the community help make PassClash more comprehensive, accurate, and helpful for everyone learning ethical hacking and security concepts.

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Table of Contents

- [Contributing to PassClash](#contributing-to-passclash)
  - [Table of Contents](#table-of-contents)
  - [How Can I Contribute?](#how-can-i-contribute)
    - [Reporting Bugs](#reporting-bugs)
    - [Suggesting Enhancements](#suggesting-enhancements)
    - [Pull Requests](#pull-requests)
  - [Development Setup](#development-setup)
    - [Prerequisites](#prerequisites)
    - [Setting Up Your Workspace](#setting-up-your-workspace)
    - [Development Commands](#development-commands)
  - [Style & Code Guidelines](#style--code-guidelines)
    - [Python Coding Style](#python-coding-style)
    - [Commit Messages](#commit-messages)
  - [Testing](#testing)
    - [Writing Unit Tests](#writing-unit-tests)
  - [Security Vulnerabilities](#security-vulnerabilities)

---

## How Can I Contribute?

### Reporting Bugs

We use structured GitHub Issues to track bug reports. Before submitting a bug report, please:

1. Check the existing issues to ensure it hasn't been reported or resolved already.
2. Test on a clean environment without conflicting browser extensions or local modifications.
3. Open a bug report including:
   - Application version/commit
   - Python version and OS details
   - Step-by-step instructions to reproduce
   - Console logs or error messages
   - Scenario configuration if applicable

### Suggesting Enhancements

If you have ideas for new scenarios, hash types, UI improvements, or educational features:

1. Search the issues to verify your suggestion hasn't been discussed before.
2. Open a Feature Request describing the functionality, the educational value it provides, and how it might be implemented.

### Pull Requests

To submit code changes:

1. **Fork** the repository and create your branch from `main` (e.g., `feat/new-scenario` or `fix/hash-bug`).
2. Make your changes, keeping them focused. Avoid unrelated changes.
3. Write clean, readable code following our guidelines.
4. Ensure your changes pass all tests and linting checks locally (`pytest && ruff check`).
5. Submit a Pull Request (PR) with a clear description of the changes and references to any related issues.

---

## Development Setup

This project is built using **Python 3.13**, **Streamlit**, and **bcrypt**.

### Prerequisites

- **Python** 3.13 or higher
- **pip** (Python package manager)
- **Git**

### Setting Up Your Workspace

1. **Clone the repository:**

   ```bash
   git clone https://github.com/BleckWolf25/PassClash.git
   cd PassClash
   ```

2. **Create a virtual environment and install dependencies:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. **Run the application:**

   ```bash
   passclash
   ```

4. Open [http://localhost:8501](http://localhost:8501) to view the application.

### Development Commands

Use the following commands in your project root:

- **Start Streamlit application:**

  ```bash
  passclash
  # or
  streamlit run passclash/app.py
  ```

- **Run linter:**

  ```bash
  ruff check
  ```

- **Format code:**

  ```bash
  ruff format
  ```

- **Run Pylint:**

  ```bash
  pylint passclash
  ```

- **Run unit tests:**

  ```bash
  pytest
  ```

- **Run tests with coverage:**

  ```bash
  pytest --cov=passclash --cov-report=html
  ```

---

## Style & Code Guidelines

### Python Coding Style

To keep the codebase uniform and easy to read:

- **Indentation:** Use 4 spaces for indentation. Do not use tabs.
- **Naming Conventions:**
  - Classes: `PascalCase`
  - Functions and Variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
  - Modules: `snake_case`
- **Line Length:** Maximum 100 characters (configured in pyproject.toml)
- **Imports:** Group imports in the following order:
  1. Standard library imports
  2. Third-party imports
  3. Local application imports
- **Type Hints:** Use Python type hints explicitly for function signatures and complex types.
- **Docstrings:** Use Google-style docstrings for functions, classes, and modules.

Example:

```python
from typing import Optional

def calculate_score(attempts: int, successes: int) -> float:
    """Calculate the success rate score.

    Args:
        attempts: Total number of attempts made.
        successes: Number of successful attempts.

    Returns:
        Success rate as a float between 0 and 1.
    """
    if attempts == 0:
        return 0.0
    return successes / attempts
```

### Commit Messages

Use prefix tags for commits, such as:

- `feat: ...` for a new feature or scenario
- `fix: ...` for a bug fix
- `docs: ...` for documentation changes
- `refactor: ...` for code style or internal design changes
- `test: ...` for adding or updating tests
- `chore: ...` for configuration/build updates

Example:

```text
feat: add support for SHA-256 hash scenarios
```

---

## Testing

This project uses pytest for unit testing.

### Writing Unit Tests

- Add test files in the `tests/` directory.
- Name test files with the `test_` prefix (e.g., `test_engine.py`).
- Use descriptive test names that explain what is being tested.
- Mock external dependencies (Streamlit, file system) when appropriate.

Example test structure:

```python
import pytest
from passclash.engine import GameEngine

def test_engine_initialization():
    """Test that the game engine initializes correctly."""
    engine = GameEngine()
    assert engine.is_active() is True
```

---

## Security Vulnerabilities

Please do not report security vulnerabilities in public issues. Refer to our [Security Policy](SECURITY.md) for instructions on how to report security issues privately.
