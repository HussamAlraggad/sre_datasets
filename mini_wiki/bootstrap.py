"""
Self-bootstrapping system for mini_wiki
Handles OS detection, virtual environment creation, and package installation
"""

import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple


class OSDetector:
    """Detect operating system and provide OS-specific commands"""

    @staticmethod
    def get_os_info() -> Tuple[str, str, str]:
        """Get OS information

        Returns:
            Tuple of (os_name, os_version, architecture)
        """
        os_name = platform.system()  # Windows, Linux, Darwin
        os_version = platform.release()
        architecture = platform.machine()

        return os_name, os_version, architecture

    @staticmethod
    def is_windows() -> bool:
        """Check if running on Windows"""
        return platform.system() == "Windows"

    @staticmethod
    def is_linux() -> bool:
        """Check if running on Linux"""
        return platform.system() == "Linux"

    @staticmethod
    def is_macos() -> bool:
        """Check if running on macOS"""
        return platform.system() == "Darwin"

    @staticmethod
    def get_python_executable() -> str:
        """Get Python executable path"""
        return sys.executable

    @staticmethod
    def get_pip_executable(venv_path: Path) -> str:
        """Get pip executable path for virtual environment

        Args:
            venv_path: Path to virtual environment

        Returns:
            Path to pip executable
        """
        if OSDetector.is_windows():
            return str(venv_path / "Scripts" / "pip.exe")
        else:
            return str(venv_path / "bin" / "pip")

    @staticmethod
    def get_python_executable_in_venv(venv_path: Path) -> str:
        """Get Python executable path in virtual environment

        Args:
            venv_path: Path to virtual environment

        Returns:
            Path to Python executable
        """
        if OSDetector.is_windows():
            return str(venv_path / "Scripts" / "python.exe")
        else:
            return str(venv_path / "bin" / "python")

    @staticmethod
    def check_python_version() -> Tuple[int, int, int]:
        """Check Python version

        Returns:
            Tuple of (major, minor, micro)
        """
        return sys.version_info[:3]

    @staticmethod
    def is_python_compatible() -> bool:
        """Check if Python version is compatible (>= 3.9)

        Returns:
            True if compatible, False otherwise
        """
        major, minor, _ = OSDetector.check_python_version()
        return (major, minor) >= (3, 9)


class VirtualEnvironmentManager:
    """Manage virtual environment creation and activation"""

    def __init__(self, work_dir: Path):
        """Initialize virtual environment manager

        Args:
            work_dir: Working directory where venv will be created
        """
        self.work_dir = Path(work_dir)
        self.venv_path = self.work_dir / ".mini_wiki_venv"

    def create_venv(self) -> bool:
        """Create virtual environment

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"Creating virtual environment at {self.venv_path}...")

            # Create venv
            subprocess.run(
                [sys.executable, "-m", "venv", str(self.venv_path)],
                check=True,
                capture_output=True,
            )

            print("✓ Virtual environment created successfully")
            return True

        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to create virtual environment: {e}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error creating virtual environment: {e}")
            return False

    def venv_exists(self) -> bool:
        """Check if virtual environment exists

        Returns:
            True if venv exists, False otherwise
        """
        return self.venv_path.exists()

    def get_pip_executable(self) -> str:
        """Get pip executable in virtual environment

        Returns:
            Path to pip executable
        """
        return OSDetector.get_pip_executable(self.venv_path)

    def get_python_executable(self) -> str:
        """Get Python executable in virtual environment

        Returns:
            Path to Python executable
        """
        return OSDetector.get_python_executable_in_venv(self.venv_path)

    def upgrade_pip(self) -> bool:
        """Upgrade pip in virtual environment

        Returns:
            True if successful, False otherwise
        """
        try:
            print("Upgrading pip...")

            subprocess.run(
                [self.get_pip_executable(), "install", "--upgrade", "pip"],
                check=True,
                capture_output=True,
            )

            print("✓ Pip upgraded successfully")
            return True

        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to upgrade pip: {e}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error upgrading pip: {e}")
            return False


class PackageInstaller:
    """Handle package installation in virtual environment"""

    def __init__(self, venv_manager: VirtualEnvironmentManager):
        """Initialize package installer

        Args:
            venv_manager: Virtual environment manager instance
        """
        self.venv_manager = venv_manager
        self.pip_executable = venv_manager.get_pip_executable()

    def install_requirements(self, requirements_file: Path) -> bool:
        """Install packages from requirements file

        Args:
            requirements_file: Path to requirements.txt

        Returns:
            True if successful, False otherwise
        """
        if not requirements_file.exists():
            print(f"✗ Requirements file not found: {requirements_file}")
            return False

        try:
            print(f"Installing packages from {requirements_file}...")

            subprocess.run(
                [self.pip_executable, "install", "-r", str(requirements_file)],
                check=True,
            )

            print("✓ Packages installed successfully")
            return True

        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install packages: {e}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error installing packages: {e}")
            return False

    def install_package(self, package_name: str) -> bool:
        """Install single package

        Args:
            package_name: Name of package to install

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"Installing {package_name}...")

            subprocess.run(
                [self.pip_executable, "install", package_name],
                check=True,
            )

            print(f"✓ {package_name} installed successfully")
            return True

        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {package_name}: {e}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error installing {package_name}: {e}")
            return False

    def install_packages(self, packages: List[str]) -> bool:
        """Install multiple packages

        Args:
            packages: List of package names

        Returns:
            True if all successful, False otherwise
        """
        all_success = True

        for package in packages:
            if not self.install_package(package):
                all_success = False

        return all_success

    def verify_installation(self, package_name: str) -> bool:
        """Verify package is installed

        Args:
            package_name: Name of package to verify

        Returns:
            True if installed, False otherwise
        """
        try:
            subprocess.run(
                [self.venv_manager.get_python_executable(), "-c", f"import {package_name}"],
                check=True,
                capture_output=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False


class BootstrapManager:
    """Main bootstrap manager orchestrating the setup process"""

    def __init__(self, work_dir: Optional[Path] = None):
        """Initialize bootstrap manager

        Args:
            work_dir: Working directory (defaults to current directory)
        """
        self.work_dir = Path(work_dir or os.getcwd())
        self.os_detector = OSDetector()
        self.venv_manager = VirtualEnvironmentManager(self.work_dir)
        self.package_installer = PackageInstaller(self.venv_manager)

    def print_header(self):
        """Print bootstrap header"""
        print("\n" + "=" * 80)
        print("mini_wiki Self-Bootstrap System")
        print("=" * 80 + "\n")

    def print_os_info(self):
        """Print OS information"""
        os_name, os_version, arch = self.os_detector.get_os_info()
        python_version = ".".join(map(str, self.os_detector.check_python_version()))

        print(f"Operating System: {os_name} {os_version}")
        print(f"Architecture: {arch}")
        print(f"Python Version: {python_version}")
        print(f"Working Directory: {self.work_dir}\n")

    def check_requirements(self) -> bool:
        """Check if system meets requirements

        Returns:
            True if requirements met, False otherwise
        """
        print("Checking system requirements...")

        # Check Python version
        if not self.os_detector.is_python_compatible():
            major, minor, _ = self.os_detector.check_python_version()
            print(f"✗ Python {major}.{minor} is not compatible (requires >= 3.9)")
            return False

        print("✓ Python version is compatible")

        # Check venv module
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", "--help"],
                check=True,
                capture_output=True,
            )
            print("✓ venv module is available")
        except subprocess.CalledProcessError:
            print("✗ venv module is not available")
            return False

        print()
        return True

    def setup_environment(self) -> bool:
        """Setup virtual environment

        Returns:
            True if successful, False otherwise
        """
        print("Setting up virtual environment...")

        # Check if venv already exists
        if self.venv_manager.venv_exists():
            print(f"✓ Virtual environment already exists at {self.venv_manager.venv_path}")
        else:
            if not self.venv_manager.create_venv():
                return False

        # Upgrade pip
        if not self.venv_manager.upgrade_pip():
            print("⚠ Warning: Failed to upgrade pip, continuing anyway...")

        print()
        return True

    def install_dependencies(self, requirements_file: Optional[Path] = None) -> bool:
        """Install dependencies

        Args:
            requirements_file: Path to requirements.txt (auto-detected if not provided)

        Returns:
            True if successful, False otherwise
        """
        print("Installing dependencies...")

        # Auto-detect requirements file
        if requirements_file is None:
            possible_locations = [
                self.work_dir / "requirements.txt",
                self.work_dir / "mini_wiki" / "requirements.txt",
                Path(__file__).parent / "requirements.txt",
            ]

            for location in possible_locations:
                if location.exists():
                    requirements_file = location
                    break

        if requirements_file is None:
            print("✗ requirements.txt not found")
            return False

        if not self.package_installer.install_requirements(requirements_file):
            return False

        print()
        return True

    def verify_installation(self) -> bool:
        """Verify critical packages are installed

        Returns:
            True if all critical packages installed, False otherwise
        """
        print("Verifying installation...")

        critical_packages = [
            "numpy",
            "pandas",
            "faiss",
            "sentence_transformers",
            "click",
            "yaml",
        ]

        all_verified = True

        for package in critical_packages:
            if self.package_installer.verify_installation(package):
                print(f"✓ {package} is installed")
            else:
                print(f"✗ {package} is NOT installed")
                all_verified = False

        print()
        return all_verified

    def bootstrap(self, requirements_file: Optional[Path] = None) -> bool:
        """Run complete bootstrap process

        Args:
            requirements_file: Path to requirements.txt (auto-detected if not provided)

        Returns:
            True if successful, False otherwise
        """
        self.print_header()
        self.print_os_info()

        # Check requirements
        if not self.check_requirements():
            print("✗ System requirements not met")
            return False

        # Setup environment
        if not self.setup_environment():
            print("✗ Failed to setup virtual environment")
            return False

        # Install dependencies
        if not self.install_dependencies(requirements_file):
            print("✗ Failed to install dependencies")
            return False

        # Verify installation
        if not self.verify_installation():
            print("⚠ Warning: Some packages failed verification")
            return False

        print("=" * 80)
        print("✓ Bootstrap completed successfully!")
        print("=" * 80 + "\n")

        return True

    def get_venv_python(self) -> str:
        """Get Python executable in virtual environment

        Returns:
            Path to Python executable
        """
        return self.venv_manager.get_python_executable()

    def get_venv_pip(self) -> str:
        """Get pip executable in virtual environment

        Returns:
            Path to pip executable
        """
        return self.venv_manager.get_pip_executable()

    def run_in_venv(self, command: List[str]) -> bool:
        """Run command in virtual environment

        Args:
            command: Command to run

        Returns:
            True if successful, False otherwise
        """
        try:
            subprocess.run(command, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Command failed: {e}")
            return False
