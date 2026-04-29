#!/usr/bin/env python3
"""
mini_wiki Installation Script
Installs mini_wiki system-wide so it can be used from anywhere

Usage:
    python install.py                    # Install to default location
    python install.py --prefix /custom   # Install to custom location
    python install.py --uninstall        # Uninstall mini_wiki
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


class MiniWikiInstaller:
    """Handle system-wide installation of mini_wiki"""

    def __init__(self, prefix: Optional[Path] = None):
        """Initialize installer

        Args:
            prefix: Installation prefix (defaults to ~/.local or %APPDATA%)
        """
        self.script_dir = Path(__file__).parent.absolute()
        self.os_name = platform.system()

        # Determine installation prefix
        if prefix:
            self.prefix = Path(prefix).expanduser().absolute()
        else:
            self.prefix = self._get_default_prefix()

        # Installation directories
        self.bin_dir = self.prefix / "bin"
        self.lib_dir = self.prefix / "lib" / "mini_wiki"
        self.config_dir = self.prefix / "etc" / "mini_wiki"

    def _get_default_prefix(self) -> Path:
        """Get default installation prefix based on OS

        Returns:
            Path to installation prefix
        """
        if self.os_name == "Windows":
            # Windows: %APPDATA%\mini_wiki
            appdata = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
            return appdata / "mini_wiki"
        else:
            # Linux/macOS: ~/.local
            return Path.home() / ".local"

    def print_header(self):
        """Print installation header"""
        print("\n" + "=" * 80)
        print("mini_wiki System-Wide Installation")
        print("=" * 80 + "\n")

    def print_info(self):
        """Print installation information"""
        print(f"Operating System: {self.os_name}")
        print(f"Installation Prefix: {self.prefix}")
        print(f"Bin Directory: {self.bin_dir}")
        print(f"Lib Directory: {self.lib_dir}")
        print(f"Config Directory: {self.config_dir}\n")

    def check_requirements(self) -> bool:
        """Check if system meets requirements

        Returns:
            True if requirements met, False otherwise
        """
        print("Checking system requirements...")

        # Check Python version
        major, minor = sys.version_info[:2]
        if (major, minor) < (3, 9):
            print(f"✗ Python {major}.{minor} is not compatible (requires >= 3.9)")
            return False

        print("✓ Python version is compatible")

        # Check write permissions
        try:
            self.prefix.mkdir(parents=True, exist_ok=True)
            test_file = self.prefix / ".write_test"
            test_file.touch()
            test_file.unlink()
            print("✓ Write permissions verified")
        except Exception as e:
            print(f"✗ No write permissions: {e}")
            return False

        print()
        return True

    def create_directories(self) -> bool:
        """Create installation directories

        Returns:
            True if successful, False otherwise
        """
        print("Creating installation directories...")

        try:
            self.bin_dir.mkdir(parents=True, exist_ok=True)
            self.lib_dir.mkdir(parents=True, exist_ok=True)
            self.config_dir.mkdir(parents=True, exist_ok=True)

            print(f"✓ Created {self.bin_dir}")
            print(f"✓ Created {self.lib_dir}")
            print(f"✓ Created {self.config_dir}")
            print()

            return True

        except Exception as e:
            print(f"✗ Failed to create directories: {e}")
            return False

    def copy_files(self) -> bool:
        """Copy mini_wiki files to installation directory

        Returns:
            True if successful, False otherwise
        """
        print("Copying mini_wiki files...")

        try:
            # Copy mini_wiki package
            src_mini_wiki = self.script_dir / "mini_wiki"
            dst_mini_wiki = self.lib_dir / "mini_wiki"

            if dst_mini_wiki.exists():
                shutil.rmtree(dst_mini_wiki)

            shutil.copytree(src_mini_wiki, dst_mini_wiki)
            print(f"✓ Copied mini_wiki package to {dst_mini_wiki}")

            # Copy configuration
            src_config = self.script_dir / "mini_wiki" / "config" / "mini_wiki_config.yaml"
            dst_config = self.config_dir / "mini_wiki_config.yaml"

            if src_config.exists():
                shutil.copy2(src_config, dst_config)
                print(f"✓ Copied configuration to {dst_config}")

            print()
            return True

        except Exception as e:
            print(f"✗ Failed to copy files: {e}")
            return False

    def create_wrapper_script(self) -> bool:
        """Create wrapper script in bin directory

        Returns:
            True if successful, False otherwise
        """
        print("Creating wrapper script...")

        try:
            if self.os_name == "Windows":
                return self._create_windows_wrapper()
            else:
                return self._create_unix_wrapper()

        except Exception as e:
            print(f"✗ Failed to create wrapper script: {e}")
            return False

    def _create_unix_wrapper(self) -> bool:
        """Create Unix/Linux/macOS wrapper script

        Returns:
            True if successful, False otherwise
        """
        wrapper_path = self.bin_dir / "mini_wiki"

        script_content = f"""#!/bin/bash
# mini_wiki - Universal Research Assistant
# Auto-generated wrapper script

MINI_WIKI_LIB="{self.lib_dir}"
MINI_WIKI_CONFIG="{self.config_dir}"

export MINI_WIKI_LIB
export MINI_WIKI_CONFIG

# Run mini_wiki
python3 "$MINI_WIKI_LIB/mini_wiki/run.py" "$@"
"""

        try:
            with open(wrapper_path, "w") as f:
                f.write(script_content)

            # Make executable
            wrapper_path.chmod(0o755)

            print(f"✓ Created wrapper script at {wrapper_path}")
            print()

            return True

        except Exception as e:
            print(f"✗ Failed to create Unix wrapper: {e}")
            return False

    def _create_windows_wrapper(self) -> bool:
        """Create Windows batch wrapper script

        Returns:
            True if successful, False otherwise
        """
        wrapper_path = self.bin_dir / "mini_wiki.bat"

        script_content = f"""@echo off
REM mini_wiki - Universal Research Assistant
REM Auto-generated wrapper script

set MINI_WIKI_LIB={self.lib_dir}
set MINI_WIKI_CONFIG={self.config_dir}

python "%MINI_WIKI_LIB%\\mini_wiki\\run.py" %*
"""

        try:
            with open(wrapper_path, "w") as f:
                f.write(script_content)

            print(f"✓ Created wrapper script at {wrapper_path}")
            print()

            return True

        except Exception as e:
            print(f"✗ Failed to create Windows wrapper: {e}")
            return False

    def update_path(self) -> bool:
        """Update system PATH to include mini_wiki bin directory

        Returns:
            True if successful, False otherwise
        """
        print("Updating system PATH...")

        if self.os_name == "Windows":
            return self._update_windows_path()
        else:
            return self._update_unix_path()

    def _update_unix_path(self) -> bool:
        """Update PATH for Unix/Linux/macOS

        Returns:
            True if successful, False otherwise
        """
        shell_rc_files = [
            Path.home() / ".bashrc",
            Path.home() / ".zshrc",
            Path.home() / ".profile",
        ]

        path_export = f'export PATH="{self.bin_dir}:$PATH"'

        for rc_file in shell_rc_files:
            if not rc_file.exists():
                continue

            try:
                with open(rc_file, "r") as f:
                    content = f.read()

                # Check if already added
                if str(self.bin_dir) in content:
                    continue

                # Add to file
                with open(rc_file, "a") as f:
                    f.write(f"\n# mini_wiki\n{path_export}\n")

                print(f"✓ Updated {rc_file}")

            except Exception as e:
                print(f"⚠ Warning: Failed to update {rc_file}: {e}")

        print()
        return True

    def _update_windows_path(self) -> bool:
        """Update PATH for Windows

        Returns:
            True if successful, False otherwise
        """
        try:
            import winreg

            # Open registry
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Environment",
                0,
                winreg.KEY_ALL_ACCESS,
            )

            # Get current PATH
            try:
                current_path, _ = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                current_path = ""

            # Add mini_wiki bin directory if not already present
            if str(self.bin_dir) not in current_path:
                new_path = f"{current_path};{self.bin_dir}"
                winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)

            winreg.CloseKey(key)

            print(f"✓ Updated Windows PATH")
            print()

            return True

        except Exception as e:
            print(f"⚠ Warning: Failed to update Windows PATH: {e}")
            print(f"  Please manually add {self.bin_dir} to your PATH")
            print()

            return True  # Don't fail installation

    def verify_installation(self) -> bool:
        """Verify installation

        Returns:
            True if successful, False otherwise
        """
        print("Verifying installation...")

        # Check if files exist
        if not (self.lib_dir / "mini_wiki").exists():
            print("✗ mini_wiki package not found")
            return False

        print("✓ mini_wiki package found")

        # Check if wrapper exists
        if self.os_name == "Windows":
            wrapper = self.bin_dir / "mini_wiki.bat"
        else:
            wrapper = self.bin_dir / "mini_wiki"

        if not wrapper.exists():
            print("✗ Wrapper script not found")
            return False

        print("✓ Wrapper script found")

        # Check if config exists
        if not (self.config_dir / "mini_wiki_config.yaml").exists():
            print("⚠ Configuration file not found (will use defaults)")
        else:
            print("✓ Configuration file found")

        print()
        return True

    def install(self) -> bool:
        """Run complete installation

        Returns:
            True if successful, False otherwise
        """
        self.print_header()
        self.print_info()

        # Check requirements
        if not self.check_requirements():
            print("✗ System requirements not met")
            return False

        # Create directories
        if not self.create_directories():
            print("✗ Failed to create directories")
            return False

        # Copy files
        if not self.copy_files():
            print("✗ Failed to copy files")
            return False

        # Create wrapper script
        if not self.create_wrapper_script():
            print("✗ Failed to create wrapper script")
            return False

        # Update PATH
        if not self.update_path():
            print("⚠ Warning: Failed to update PATH")

        # Verify installation
        if not self.verify_installation():
            print("✗ Installation verification failed")
            return False

        print("=" * 80)
        print("✓ Installation completed successfully!")
        print("=" * 80 + "\n")

        self._print_next_steps()

        return True

    def uninstall(self) -> bool:
        """Uninstall mini_wiki

        Returns:
            True if successful, False otherwise
        """
        self.print_header()
        print(f"Uninstalling from: {self.prefix}\n")

        try:
            # Remove installation directory
            if self.lib_dir.exists():
                shutil.rmtree(self.lib_dir)
                print(f"✓ Removed {self.lib_dir}")

            # Remove config directory
            if self.config_dir.exists():
                shutil.rmtree(self.config_dir)
                print(f"✓ Removed {self.config_dir}")

            # Remove wrapper script
            if self.os_name == "Windows":
                wrapper = self.bin_dir / "mini_wiki.bat"
            else:
                wrapper = self.bin_dir / "mini_wiki"

            if wrapper.exists():
                wrapper.unlink()
                print(f"✓ Removed {wrapper}")

            print()
            print("=" * 80)
            print("✓ Uninstallation completed successfully!")
            print("=" * 80 + "\n")

            return True

        except Exception as e:
            print(f"✗ Uninstallation failed: {e}")
            return False

    def _print_next_steps(self):
        """Print next steps after installation"""
        print("Next steps:")
        print()

        if self.os_name == "Windows":
            print("1. Open a new Command Prompt or PowerShell window")
            print("2. Run: mini_wiki --help")
            print("3. Run: mini_wiki tui")
        else:
            print("1. Open a new terminal window")
            print("2. Run: mini_wiki --help")
            print("3. Run: mini_wiki tui")

        print()
        print("You can now use mini_wiki from anywhere on your system!")
        print()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Install mini_wiki system-wide",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python install.py                    # Install to default location
  python install.py --prefix /custom   # Install to custom location
  python install.py --uninstall        # Uninstall mini_wiki
        """,
    )

    parser.add_argument(
        "--prefix",
        type=str,
        default=None,
        help="Installation prefix (default: ~/.local or %%APPDATA%%)",
    )

    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall mini_wiki",
    )

    args = parser.parse_args()

    # Create installer
    installer = MiniWikiInstaller(prefix=args.prefix)

    # Run installation or uninstallation
    if args.uninstall:
        success = installer.uninstall()
    else:
        success = installer.install()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
