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
    cp mini_wiki /usr/local/bin/   # or ~/bin/
    mini_wiki --tui
"""

import os
import sys
from pathlib import Path

# Resolve the project directory (where this script lives)
SCRIPT_DIR = Path(__file__).resolve().parent
MINI_WIKI_DIR = SCRIPT_DIR / "mini_wiki"

# Add to Python path so imports work from any directory
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(MINI_WIKI_DIR))

# Set working directory to project root for data/config resolution
os.chdir(SCRIPT_DIR)

# Now run the actual entry point
from mini_wiki.run_interactive import main

if __name__ == "__main__":
    main()