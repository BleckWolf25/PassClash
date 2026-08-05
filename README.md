# PassClash

> A password-cracking red/blue team simulation for ethical-hacking training. Pure Python + Streamlit

PassClash is an educational security simulation that pits Red Team (password crackers) against Blue Team (defenders) in real-time. Crack a simulated hash dump as Red Team while Blue Team detects and mitigates attacks — all in a safe, controlled environment for learning ethical hacking techniques.

## 🚀 Getting Started

### Prerequisites

- **Python** 3.13 or higher
- **pip** (Python package manager)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/BleckWolf25/PassClash.git
   cd PassClash
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e .
   ```

3. Run the application:

   ```bash
   passclash
   ```

4. Open [http://localhost:8501](http://localhost:8501) with your browser to see the application.

   Open multiple browser tabs pointing at the same URL: one plays Red Team, another Blue Team, and optionally a third as Game Master.

## 📝 Available Scripts

- `passclash` - Start the Streamlit application (after `pip install -e .`)
- `streamlit run passclash/app.py` - Alternative way to start the application
- `pytest` - Run unit tests
- `ruff check` - Run Ruff linter
- `ruff format` - Format code with Ruff
- `pylint passclash` - Run Pylint linter

## 🏗️ Project Structure

```zsh
PassClash/
├── passclash/              # Main package directory
│   ├── __init__.py        # Package initialization
│   ├── app.py             # Streamlit entry point and CLI
│   ├── engine.py          # Core simulation engine
│   ├── events.py          # Event handling system
│   ├── hashes.py          # Hash generation and verification
│   ├── scenario.py        # Scenario configuration
│   ├── scoring.py         # Red/blue team scoring logic
│   ├── state.py           # Application state management
│   ├── terminal.py        # Terminal UI components
│   └── ui/                # User interface components
│       ├── __init__.py
│       ├── blueteam.py    # Blue Team interface
│       ├── common.py      # Shared UI components
│       ├── gm.py          # Game Master interface
│       └── redteam.py     # Red Team interface
├── scenarios/             # Scenario configuration files
│   └── default.json       # Default training scenario
├── scripts/               # Utility scripts
│   ├── generate_wordlist.py
│   └── make_scenario.py
├── tests/                 # Unit tests
│   ├── conftest.py
│   ├── test_app.py
│   ├── test_engine.py
│   ├── test_hashes.py
│   └── test test_scoring.py
├── wordlists/            # Password wordlists
│   └── rockyou_top5k.txt
├── pyproject.toml        # Project configuration
└── README.md             # This file
```

## 🧪 Testing

The project uses pytest for unit testing.

### Run Unit Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=passclash --cov-report=html
```

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting a pull request.

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔒 Security

For security concerns, please review our [Security Policy](SECURITY.md).

## 📧 Contact

For questions or support, please open an issue on GitHub or contact [joao.coutinho08@icloud.com](mailto:joao.coutinho08@icloud.com).

---

Built with ❤️ using Python, Streamlit, and bcrypt
