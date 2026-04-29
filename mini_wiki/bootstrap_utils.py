"""
Bootstrap utilities and helpers
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional


class BootstrapConfig:
    """Configuration for bootstrap process"""

    # Minimum Python version
    MIN_PYTHON_VERSION = (3, 9)

    # Critical packages that must be installed
    CRITICAL_PACKAGES = [
        "numpy",
        "pandas",
        "faiss",
        "sentence_transformers",
        "click",
        "yaml",
    ]

    # Optional packages (nice to have but not critical)
    OPTIONAL_PACKAGES = [
        "pytest",
        "black",
        "flake8",
    ]

    # Virtual environment directory name
    VENV_DIR_NAME = ".mini_wiki_venv"

    # Requirements file name
    REQUIREMENTS_FILE = "requirements.txt"

    # Bootstrap state file
    STATE_FILE = ".mini_wiki_bootstrap_state.json"


class BootstrapState:
    """Manage bootstrap state persistence"""

    def __init__(self, work_dir: Path):
        """Initialize bootstrap state manager

        Args:
            work_dir: Working directory
        """
        self.work_dir = Path(work_dir)
        self.state_file = self.work_dir / BootstrapConfig.STATE_FILE

    def load_state(self) -> Dict[str, Any]:
        """Load bootstrap state from file

        Returns:
            State dictionary
        """
        if not self.state_file.exists():
            return {}

        try:
            with open(self.state_file, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_state(self, state: Dict[str, Any]) -> None:
        """Save bootstrap state to file

        Args:
            state: State dictionary
        """
        try:
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception:
            pass

    def is_bootstrapped(self) -> bool:
        """Check if already bootstrapped

        Returns:
            True if bootstrapped, False otherwise
        """
        state = self.load_state()
        return state.get("bootstrapped", False)

    def mark_bootstrapped(self) -> None:
        """Mark as bootstrapped"""
        state = self.load_state()
        state["bootstrapped"] = True
        state["python_version"] = sys.version
        state["platform"] = sys.platform
        self.save_state(state)

    def get_last_bootstrap_time(self) -> Optional[str]:
        """Get last bootstrap time

        Returns:
            Timestamp or None
        """
        state = self.load_state()
        return state.get("last_bootstrap_time")


class PackageManager:
    """Manage package information and installation"""

    @staticmethod
    def get_installed_packages(pip_executable: str) -> Dict[str, str]:
        """Get list of installed packages

        Args:
            pip_executable: Path to pip executable

        Returns:
            Dictionary of package names and versions
        """
        try:
            output = subprocess.check_output(
                [pip_executable, "list", "--format", "json"],
                text=True,
            )
            packages = json.loads(output)
            return {pkg["name"]: pkg["version"] for pkg in packages}
        except Exception:
            return {}

    @staticmethod
    def get_package_version(pip_executable: str, package_name: str) -> Optional[str]:
        """Get installed version of package

        Args:
            pip_executable: Path to pip executable
            package_name: Name of package

        Returns:
            Version string or None
        """
        packages = PackageManager.get_installed_packages(pip_executable)
        return packages.get(package_name)

    @staticmethod
    def check_package_compatibility(pip_executable: str, package_name: str, required_version: str) -> bool:
        """Check if package version meets requirement

        Args:
            pip_executable: Path to pip executable
            package_name: Name of package
            required_version: Required version (e.g., ">=1.0.0")

        Returns:
            True if compatible, False otherwise
        """
        # Simplified version check (in production, use packaging.version)
        installed = PackageManager.get_package_version(pip_executable, package_name)
        return installed is not None


class EnvironmentValidator:
    """Validate environment and system requirements"""

    @staticmethod
    def validate_python_version() -> bool:
        """Validate Python version

        Returns:
            True if valid, False otherwise
        """
        major, minor = sys.version_info[:2]
        min_major, min_minor = BootstrapConfig.MIN_PYTHON_VERSION
        return (major, minor) >= (min_major, min_minor)

    @staticmethod
    def validate_write_permissions(path: Path) -> bool:
        """Validate write permissions for directory

        Args:
            path: Directory path

        Returns:
            True if writable, False otherwise
        """
        try:
            test_file = path / ".mini_wiki_write_test"
            test_file.touch()
            test_file.unlink()
            return True
        except Exception:
            return False

    @staticmethod
    def validate_disk_space(path: Path, required_mb: int = 500) -> bool:
        """Validate available disk space

        Args:
            path: Directory path
            required_mb: Required space in MB

        Returns:
            True if enough space, False otherwise
        """
        try:
            import shutil

            stat = shutil.disk_usage(path)
            available_mb = stat.free / (1024 * 1024)
            return available_mb >= required_mb
        except Exception:
            return True  # Assume OK if can't check


class ProgressTracker:
    """Track bootstrap progress"""

    def __init__(self):
        """Initialize progress tracker"""
        self.steps = []
        self.current_step = 0

    def add_step(self, name: str, description: str = "") -> None:
        """Add a step to track

        Args:
            name: Step name
            description: Step description
        """
        self.steps.append({"name": name, "description": description, "status": "pending"})

    def start_step(self, step_index: int) -> None:
        """Mark step as started

        Args:
            step_index: Index of step
        """
        if 0 <= step_index < len(self.steps):
            self.steps[step_index]["status"] = "in_progress"
            self.current_step = step_index

    def complete_step(self, step_index: int) -> None:
        """Mark step as completed

        Args:
            step_index: Index of step
        """
        if 0 <= step_index < len(self.steps):
            self.steps[step_index]["status"] = "completed"

    def fail_step(self, step_index: int) -> None:
        """Mark step as failed

        Args:
            step_index: Index of step
        """
        if 0 <= step_index < len(self.steps):
            self.steps[step_index]["status"] = "failed"

    def get_progress(self) -> float:
        """Get progress percentage

        Returns:
            Progress as percentage (0-100)
        """
        if not self.steps:
            return 0.0

        completed = sum(1 for s in self.steps if s["status"] == "completed")
        return (completed / len(self.steps)) * 100

    def print_progress(self) -> None:
        """Print progress summary"""
        print("\nBootstrap Progress:")
        print("-" * 60)

        for i, step in enumerate(self.steps):
            status_symbol = {
                "pending": "○",
                "in_progress": "◐",
                "completed": "●",
                "failed": "✗",
            }.get(step["status"], "?")

            print(f"{status_symbol} {step['name']}")

        print("-" * 60)
        print(f"Progress: {self.get_progress():.0f}%\n")


class ColorOutput:
    """Colored terminal output"""

    # ANSI color codes
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    @staticmethod
    def success(message: str) -> str:
        """Format success message

        Args:
            message: Message text

        Returns:
            Formatted message
        """
        return f"{ColorOutput.GREEN}✓ {message}{ColorOutput.RESET}"

    @staticmethod
    def error(message: str) -> str:
        """Format error message

        Args:
            message: Message text

        Returns:
            Formatted message
        """
        return f"{ColorOutput.RED}✗ {message}{ColorOutput.RESET}"

    @staticmethod
    def warning(message: str) -> str:
        """Format warning message

        Args:
            message: Message text

        Returns:
            Formatted message
        """
        return f"{ColorOutput.YELLOW}⚠ {message}{ColorOutput.RESET}"

    @staticmethod
    def info(message: str) -> str:
        """Format info message

        Args:
            message: Message text

        Returns:
            Formatted message
        """
        return f"{ColorOutput.CYAN}ℹ {message}{ColorOutput.RESET}"

    @staticmethod
    def header(message: str) -> str:
        """Format header message

        Args:
            message: Message text

        Returns:
            Formatted message
        """
        return f"{ColorOutput.BOLD}{ColorOutput.BLUE}{message}{ColorOutput.RESET}"
