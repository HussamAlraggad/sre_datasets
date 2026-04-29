#!/usr/bin/env python3
"""
mini_wiki - Universal Research Assistant
Self-bootstrapping entry point

This script handles:
1. OS detection
2. Virtual environment creation
3. Package installation
4. Application launch
"""

import os
import sys
from pathlib import Path


def main():
    """Main entry point"""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()

    # Add script directory to Python path
    sys.path.insert(0, str(script_dir))

    # Import bootstrap system
    try:
        from bootstrap import BootstrapManager
    except ImportError:
        print("✗ Failed to import bootstrap module")
        sys.exit(1)

    # Get working directory (where mini_wiki is run from)
    work_dir = Path.cwd()

    # Initialize bootstrap manager
    bootstrap = BootstrapManager(work_dir)

    # Run bootstrap process
    if not bootstrap.bootstrap():
        print("✗ Bootstrap failed")
        sys.exit(1)

    # Now import and run the main application
    try:
        # Add venv to path
        venv_python = bootstrap.get_venv_python()
        venv_site_packages = Path(venv_python).parent.parent / "lib"

        if not venv_site_packages.exists():
            # Windows path
            venv_site_packages = Path(venv_python).parent.parent / "Lib"

        sys.path.insert(0, str(venv_site_packages))

        # Import main application
        from mini_wiki.main import cli

        # Run CLI
        cli()

    except ImportError as e:
        print(f"✗ Failed to import mini_wiki: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
