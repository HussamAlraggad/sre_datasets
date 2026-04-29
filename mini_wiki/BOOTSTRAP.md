# mini_wiki Bootstrap System Documentation

## Overview

The mini_wiki bootstrap system is a self-contained installation and environment management system that:

1. **Detects the operating system** (Windows, Linux, macOS)
2. **Validates system requirements** (Python 3.9+, venv module)
3. **Creates isolated virtual environment** in the working directory
4. **Installs all dependencies** automatically
5. **Verifies installation** of critical packages
6. **Launches the application** seamlessly

This ensures mini_wiki works out-of-the-box on any system without manual configuration.

---

## Architecture

### Components

```
bootstrap.py
├── OSDetector
│   ├── get_os_info()
│   ├── is_windows/linux/macos()
│   ├── get_python_executable()
│   ├── get_pip_executable()
│   └── check_python_version()
│
├── VirtualEnvironmentManager
│   ├── create_venv()
│   ├── venv_exists()
│   ├── get_pip_executable()
│   ├── get_python_executable()
│   └── upgrade_pip()
│
├── PackageInstaller
│   ├── install_requirements()
│   ├── install_package()
│   ├── install_packages()
│   └── verify_installation()
│
└── BootstrapManager
    ├── check_requirements()
    ├── setup_environment()
    ├── install_dependencies()
    ├── verify_installation()
    └── bootstrap()

bootstrap_utils.py
├── BootstrapConfig
├── BootstrapState
├── PackageManager
├── EnvironmentValidator
├── ProgressTracker
└── ColorOutput

run.py
└── main() - Entry point

mini_wiki.sh - Unix wrapper
mini_wiki.bat - Windows wrapper
```

---

## Execution Flow

### 1. User Runs mini_wiki

```bash
./mini_wiki.sh              # Linux/macOS
# or
mini_wiki.bat               # Windows
# or
python run.py               # Any OS
```

### 2. OS Detection

```
Operating System: Linux
Architecture: x86_64
Python Version: 3.10.0
Working Directory: /home/user/mini_wiki
```

### 3. System Requirements Check

```
✓ Python version is compatible (3.10.0 >= 3.9)
✓ venv module is available
✓ Write permissions verified
✓ Disk space available (500MB+)
```

### 4. Virtual Environment Setup

```
Creating virtual environment at /home/user/mini_wiki/.mini_wiki_venv...
✓ Virtual environment created successfully
✓ Pip upgraded successfully
```

### 5. Package Installation

```
Installing packages from requirements.txt...
Installing numpy==1.21.0...
Installing pandas==1.3.0...
Installing faiss-cpu==1.7.0...
[... more packages ...]
✓ Packages installed successfully
```

### 6. Installation Verification

```
Verifying installation...
✓ numpy is installed
✓ pandas is installed
✓ faiss is installed
✓ sentence_transformers is installed
✓ click is installed
✓ yaml is installed
```

### 7. Application Launch

```
✓ Bootstrap completed successfully!
[mini_wiki CLI starts]
```

---

## OS-Specific Implementation

### Windows

**Virtual Environment Paths**:
```
.mini_wiki_venv\Scripts\python.exe
.mini_wiki_venv\Scripts\pip.exe
.mini_wiki_venv\Lib\site-packages\
```

**Entry Point**: `mini_wiki.bat`

**Features**:
- Batch script wrapper with error handling
- Automatic Python detection
- Version validation
- Graceful error messages

### Linux

**Virtual Environment Paths**:
```
.mini_wiki_venv/bin/python
.mini_wiki_venv/bin/pip
.mini_wiki_venv/lib/python3.x/site-packages/
```

**Entry Point**: `mini_wiki.sh`

**Features**:
- Bash script wrapper
- Python3 detection
- Version validation
- Portable across distributions

### macOS

**Virtual Environment Paths**:
```
.mini_wiki_venv/bin/python
.mini_wiki_venv/bin/pip
.mini_wiki_venv/lib/python3.x/site-packages/
```

**Entry Point**: `mini_wiki.sh`

**Features**:
- Same as Linux
- Works with system Python and Homebrew Python
- Handles M1/M2 architecture

---

## Key Classes

### OSDetector

Detects operating system and provides OS-specific paths.

```python
from bootstrap import OSDetector

# Get OS info
os_name, os_version, arch = OSDetector.get_os_info()
# Returns: ('Linux', '5.10.0', 'x86_64')

# Check OS type
if OSDetector.is_windows():
    print("Running on Windows")

# Get Python version
major, minor, micro = OSDetector.check_python_version()
# Returns: (3, 10, 0)

# Check compatibility
if OSDetector.is_python_compatible():
    print("Python version is compatible")

# Get executable paths
python_exe = OSDetector.get_python_executable()
pip_exe = OSDetector.get_pip_executable(venv_path)
```

### VirtualEnvironmentManager

Creates and manages virtual environments.

```python
from pathlib import Path
from bootstrap import VirtualEnvironmentManager

# Initialize
venv_mgr = VirtualEnvironmentManager(Path.cwd())

# Create venv
if venv_mgr.create_venv():
    print("Venv created successfully")

# Check if exists
if venv_mgr.venv_exists():
    print("Venv already exists")

# Get executables
python_exe = venv_mgr.get_python_executable()
pip_exe = venv_mgr.get_pip_executable()

# Upgrade pip
venv_mgr.upgrade_pip()
```

### PackageInstaller

Installs and verifies packages.

```python
from pathlib import Path
from bootstrap import VirtualEnvironmentManager, PackageInstaller

# Initialize
venv_mgr = VirtualEnvironmentManager(Path.cwd())
installer = PackageInstaller(venv_mgr)

# Install from requirements
installer.install_requirements(Path("requirements.txt"))

# Install single package
installer.install_package("numpy")

# Install multiple packages
installer.install_packages(["numpy", "pandas", "scipy"])

# Verify installation
if installer.verify_installation("numpy"):
    print("numpy is installed")
```

### BootstrapManager

Orchestrates the complete bootstrap process.

```python
from pathlib import Path
from bootstrap import BootstrapManager

# Initialize
bootstrap = BootstrapManager(Path.cwd())

# Run complete bootstrap
if bootstrap.bootstrap():
    print("Bootstrap successful")
    
    # Get venv executables
    python_exe = bootstrap.get_venv_python()
    pip_exe = bootstrap.get_venv_pip()
    
    # Run command in venv
    bootstrap.run_in_venv(["python", "script.py"])
```

---

## Configuration

### BootstrapConfig

```python
from bootstrap_utils import BootstrapConfig

# Minimum Python version
BootstrapConfig.MIN_PYTHON_VERSION  # (3, 9)

# Critical packages
BootstrapConfig.CRITICAL_PACKAGES
# ['numpy', 'pandas', 'faiss', 'sentence_transformers', 'click', 'yaml']

# Virtual environment directory
BootstrapConfig.VENV_DIR_NAME  # '.mini_wiki_venv'

# Requirements file
BootstrapConfig.REQUIREMENTS_FILE  # 'requirements.txt'
```

---

## State Management

### BootstrapState

Persists bootstrap state to avoid redundant operations.

```python
from pathlib import Path
from bootstrap_utils import BootstrapState

# Initialize
state = BootstrapState(Path.cwd())

# Check if already bootstrapped
if state.is_bootstrapped():
    print("Already bootstrapped")

# Mark as bootstrapped
state.mark_bootstrapped()

# Get last bootstrap time
last_time = state.get_last_bootstrap_time()
```

**State File**: `.mini_wiki_bootstrap_state.json`

```json
{
  "bootstrapped": true,
  "python_version": "3.10.0 (default, Oct  5 2021, 00:00:00) \n[GCC 11.2.0]",
  "platform": "linux",
  "last_bootstrap_time": "2024-04-29T10:30:00"
}
```

---

## Error Handling

### Error Types

1. **Python Version Error**
   ```
   ✗ Python 3.8 is not compatible (requires >= 3.9)
   ```

2. **venv Module Error**
   ```
   ✗ venv module is not available
   ```

3. **Virtual Environment Creation Error**
   ```
   ✗ Failed to create virtual environment: [error details]
   ```

4. **Package Installation Error**
   ```
   ✗ Failed to install packages: [error details]
   ```

5. **Verification Error**
   ```
   ✗ numpy is NOT installed
   ```

### Recovery Strategies

1. **Automatic Retry**
   - Failed pip operations retry once
   - Network timeouts handled gracefully

2. **Partial Failure Handling**
   - Non-critical packages can fail
   - Critical packages must succeed

3. **Cleanup on Failure**
   - Incomplete venv can be removed
   - User can retry bootstrap

---

## Performance Optimization

### First Run

- **Time**: 2-5 minutes
- **Network**: ~300MB download
- **Disk**: ~500MB for venv + packages

### Subsequent Runs

- **Time**: < 1 second (venv exists)
- **Network**: No downloads
- **Disk**: No additional space

### Optimization Techniques

1. **Batch Installation**
   - Install all packages in one pip call
   - Reduces overhead

2. **Caching**
   - pip cache used automatically
   - Faster reinstalls

3. **Lazy Loading**
   - Only verify critical packages
   - Skip optional packages if not needed

---

## Security Considerations

### Isolation

- ✅ Virtual environment completely isolated
- ✅ No system Python pollution
- ✅ Easy to audit installed packages
- ✅ Can be deleted without affecting system

### Package Verification

- ✅ Critical packages verified after installation
- ✅ Version pinning in requirements.txt
- ✅ Checksum verification (future enhancement)

### Permissions

- ✅ Write permission check before venv creation
- ✅ Proper file permissions on venv
- ✅ No sudo required (user-level installation)

---

## Troubleshooting

### Issue: "Python is not installed"

**Cause**: Python not in PATH or not installed

**Solution**:
```bash
# Check Python installation
python3 --version

# If not found, install Python 3.9+
# Linux: sudo apt-get install python3.9
# macOS: brew install python@3.9
# Windows: Download from python.org
```

### Issue: "venv module is not available"

**Cause**: Python installed without venv

**Solution**:
```bash
# Linux
sudo apt-get install python3.9-venv

# macOS (usually included)
brew install python@3.9

# Windows (check "Install pip" during installation)
```

### Issue: "Permission denied"

**Cause**: No write permissions in directory

**Solution**:
```bash
# Check permissions
ls -ld mini_wiki/

# Fix permissions
chmod u+w mini_wiki/
```

### Issue: "Virtual environment creation failed"

**Cause**: Insufficient disk space or permissions

**Solution**:
```bash
# Check disk space
df -h

# Check write permissions
touch mini_wiki/test.txt && rm mini_wiki/test.txt

# Try again
python run.py
```

### Issue: "Package installation failed"

**Cause**: Network issue or package unavailable

**Solution**:
```bash
# Check internet connection
ping google.com

# Remove incomplete venv and retry
rm -rf mini_wiki/.mini_wiki_venv
python run.py

# Or install manually
source mini_wiki/.mini_wiki_venv/bin/activate
pip install -r mini_wiki/requirements.txt
```

---

## Advanced Usage

### Custom Bootstrap Configuration

```python
from pathlib import Path
from bootstrap import BootstrapManager

# Custom working directory
bootstrap = BootstrapManager(Path("/custom/path"))

# Custom requirements file
bootstrap.bootstrap(requirements_file=Path("/custom/requirements.txt"))
```

### Manual Virtual Environment

```bash
# Create venv manually
python3 -m venv /custom/path/.mini_wiki_venv

# Activate venv
source /custom/path/.mini_wiki_venv/bin/activate

# Install packages
pip install -r requirements.txt

# Run mini_wiki
python run.py
```

### Environment Variables

```bash
# Override venv location
export MINI_WIKI_VENV=/custom/venv/path
python run.py

# Override config location
export MINI_WIKI_CONFIG=/custom/config.yaml
python run.py
```

---

## Testing Bootstrap System

### Unit Tests

```python
import pytest
from pathlib import Path
from bootstrap import OSDetector, VirtualEnvironmentManager

def test_os_detection():
    os_name, os_version, arch = OSDetector.get_os_info()
    assert os_name in ["Windows", "Linux", "Darwin"]

def test_python_version():
    assert OSDetector.is_python_compatible()

def test_venv_creation(tmp_path):
    venv_mgr = VirtualEnvironmentManager(tmp_path)
    assert venv_mgr.create_venv()
    assert venv_mgr.venv_exists()
```

### Integration Tests

```python
def test_full_bootstrap(tmp_path):
    bootstrap = BootstrapManager(tmp_path)
    assert bootstrap.bootstrap()
    assert bootstrap.venv_manager.venv_exists()
```

---

## Future Enhancements

1. **Checksum Verification**
   - Verify package integrity
   - Detect corrupted downloads

2. **Proxy Support**
   - Handle corporate proxies
   - Custom certificate support

3. **Offline Mode**
   - Pre-downloaded packages
   - Fallback to local cache

4. **Progress Visualization**
   - Progress bars
   - Real-time download speed

5. **Automatic Updates**
   - Check for package updates
   - Upgrade mechanism

6. **Multi-Python Support**
   - Support multiple Python versions
   - Version switching

---

## Conclusion

The mini_wiki bootstrap system provides a seamless, automatic installation experience that works across all major operating systems. Users can simply run the tool and it handles all setup automatically, making mini_wiki truly portable and user-friendly.

For more information, see:
- [Installation Guide](INSTALLATION.md)
- [README](README.md)
- [Architecture Guide](../ARCHITECTURE.md)
