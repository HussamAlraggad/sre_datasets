#!/bin/bash
# mini_wiki - Universal Research Assistant
# Self-bootstrapping entry point for Unix-like systems (Linux, macOS)

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 is not installed"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "✗ Python $PYTHON_VERSION is not compatible (requires >= $REQUIRED_VERSION)"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION is compatible"

# Run the Python bootstrap script
python3 "$SCRIPT_DIR/run.py" "$@"
