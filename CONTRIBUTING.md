# Contributing to KiPowerSI Pro

Thank you for your interest in contributing to **KiPowerSI Pro**! We welcome contributions from the open-source community, academic researchers, and electronic design automation (EDA) developers.

---

## How to Contribute

### 1. Reporting Bugs
If you find a bug or issue while using the plugin inside KiCad 9:
- Search existing GitHub Issues to see if it has already been reported.
- If not, open a new Issue providing:
  - KiCad Version (e.g., KiCad 9.0.1)
  - Operating System (Windows / Linux / macOS)
  - Python Version
  - Steps to reproduce & attached PCB file (if applicable)

### 2. Submitting Pull Requests
1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/anurag-thakur-2007/KiCad-Plugin-Development.git
   ```
3. Create a feature branch:
   ```bash
   git checkout -b feature/new-solver-feature
   ```
4. Make your changes and write unit tests in `tests/`.
5. Run the test suite to ensure all tests pass:
   ```bash
   python -m unittest discover -s tests -v
   ```
6. Commit your changes with clear messages and submit a Pull Request.

---

## Code Style & Guidelines

- **PEP 8**: Follow standard Python formatting.
- **Documentation**: Write clear docstrings for all new functions and classes.
- **Zero-Dependency Fallback**: Ensure any external library import (e.g., `numpy`, `scipy`) includes a pure-Python fallback.
- **KiCad 9 Compatibility**: Test plugin execution using the `pcbnew` Python API.

Thank you for making open-source EDA tools better!
