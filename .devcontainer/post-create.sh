#!/usr/bin/env bash
# Install the project exactly as contributors use it, including test and lint tools.
set -euo pipefail

python --version
python -m pip install --editable ".[dev]"
