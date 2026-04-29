#!/usr/bin/env python3
"""
mini_wiki - Universal Research Assistant
Top-level entry point that works from any directory

Usage:
    ./mini_wiki              # Interactive mode (default)
    ./mini_wiki --tui        # TUI mode (curses-based)
    ./mini_wiki --demo       # Demo mode
    ./mini_wiki search "ml"  # Quick search
    ./mini_wiki version      # Show version

Or add to PATH:
    cp mini_wiki /usr/local/bin/   # or ~/.local/bin/
    mini_wiki --tui
"""

import os
import subprocess
import sys
from pathlib import Path

# Resolve the project directory (where this script lives)
SCRIPT_DIR = Path(__file__).resolve().parent
VENV_DIR = SCRIPT_DIR / ".mini_wiki_venv"
MINI_WIKI_DIR = SCRIPT_DIR / "mini_wiki"

# Find the right Python: prefer venv, fall back to system
if (VENV_DIR / "bin" / "python3").exists():
    VENV_PYTHON = str(VENV_DIR / "bin" / "python3")
else:
    VENV_PYTHON = sys.executable


def check_and_install_deps():
    """Check if core dependencies are installed, install if not."""
    try:
        result = subprocess.run(
            [VENV_PYTHON, "-c", "import numpy, pandas, sklearn, faiss"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return True  # All good
    except Exception:
        pass

    # Dependencies missing — try to install them
    print("=" * 60)
    print("  mini_wiki - First Run Setup")
    print("  Installing dependencies...")
    print("=" * 60)

    # Make sure venv exists
    if not VENV_DIR.exists():
        print("Creating virtual environment...")
        subprocess.run(
            [sys.executable, "-m", "venv", "--without-pip", "--system-site-packages", str(VENV_DIR)],
            check=True,
        )
        # Bootstrap pip
        subprocess.run(
            [VENV_PYTHON, "-c",
             "from urllib.request import urlopen; open('/tmp/get-pip.py','wb').write(urlopen('https://bootstrap.pypa.io/get-pip.py').read())"],
            check=True,
        )
        subprocess.run([VENV_PYTHON, "/tmp/get-pip.py"], check=True)

    # Install core packages
    print("Installing core packages (numpy, pandas, scikit-learn, faiss-cpu)...")
    pip_path = str(VENV_DIR / "bin" / "pip")
    subprocess.run([pip_path, "install", "numpy", "pandas", "scikit-learn", "faiss-cpu",
                     "pyyaml", "click", "requests", "beautifulsoup4"], check=True)

    print("Installing sentence-transformers (this may take a few minutes)...")
    subprocess.run([pip_path, "install", "torch", "--index-url",
                     "https://download.pytorch.org/whl/cpu"], check=True)
    subprocess.run([pip_path, "install", "sentence-transformers",
                     "huggingface-hub", "tqdm", "transformers"], check=True)

    print()
    print("  ✓ All dependencies installed!")
    print("=" * 60)
    return True


def main():
    """Main entry point — re-executes using venv Python if needed."""
    # If we're NOT running in the venv, re-exec using venv Python
    if sys.executable != VENV_PYTHON and (VENV_DIR / "bin" / "python3").exists():
        os.execv(VENV_PYTHON, [VENV_PYTHON] + sys.argv)

    # Add project to path
    sys.path.insert(0, str(SCRIPT_DIR))
    sys.path.insert(0, str(MINI_WIKI_DIR))
    os.chdir(SCRIPT_DIR)

    # Check dependencies
    check_and_install_deps()

    # Run the actual entry point
    from mini_wiki.run_interactive import main as run_main
    run_main()


if __name__ == "__main__":
    main()