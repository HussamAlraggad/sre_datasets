# mini_wiki Installation Guide

## Overview

mini_wiki features a **self-bootstrapping system** that automatically:

1. ✅ Detects your operating system (Windows, Linux, macOS)
2. ✅ Checks Python version compatibility (requires Python 3.9+)
3. ✅ Creates an isolated virtual environment in the working directory
4. ✅ Installs all required packages automatically
5. ✅ Verifies the installation
6. ✅ Launches the application

**No manual setup required!** Just run the tool and it handles everything.

---

## Quick Start

### Option 1: Using Shell Script (Linux/macOS)

```bash
# Clone or download mini_wiki
cd mini_wiki

# Make the script executable
chmod +x mini_wiki.sh

# Run mini_wiki (bootstrap happens automatically)
./mini_wiki.sh
```

### Option 2: Using Batch Script (Windows)

```cmd
# Open Command Prompt or PowerShell
cd mini_wiki

# Run mini_wiki (bootstrap happens automatically)
mini_wiki.bat
```

### Option 3: Using Python Directly

```bash
# Any OS
cd mini_wiki
python run.py
```

---

## What Happens During Bootstrap

### Step 1: System Detection

```
Operating System: Linux
Architecture: x86_64
Python Version: 3.10.0
Working Directory: /home/user/mini_wiki
```

### Step 2: Requirements Check

- ✓ Python version >= 3.9
- ✓ venv module available
- ✓ Write permissions in working directory

### Step 3: Virtual Environment Creation

```
Creating virtual environment at /home/user/mini_wiki/.mini_wiki_venv...
✓ Virtual environment created successfully
✓ Pip upgraded successfully
```

### Step 4: Package Installation

```
Installing packages from requirements.txt...
Installing numpy...
Installing pandas...
Installing faiss-cpu...
Installing sentence-transformers...
[... more packages ...]
✓ Packages installed successfully
```

### Step 5: Installation Verification

```
Verifying installation...
✓ numpy is installed
✓ pandas is installed
✓ faiss is installed
✓ sentence_transformers is installed
✓ click is installed
✓ yaml is installed
```

### Step 6: Application Launch

```
✓ Bootstrap completed successfully!
[mini_wiki CLI starts]
```

---

## Virtual Environment Details

### Location

The virtual environment is created in a hidden directory within your working directory:

```
mini_wiki/
├── .mini_wiki_venv/          # Virtual environment (hidden)
│   ├── bin/                  # Executables (Linux/macOS)
│   ├── Scripts/              # Executables (Windows)
│   ├── lib/                  # Python packages
│   └── pyvenv.cfg            # Configuration
├── mini_wiki/                # Application code
├── config/                   # Configuration files
├── run.py                    # Bootstrap script
├── mini_wiki.sh              # Shell wrapper
└── mini_wiki.bat             # Batch wrapper
```

### Isolation

- **Completely isolated**: All packages installed in `.mini_wiki_venv/`
- **No system pollution**: Doesn't affect your system Python
- **Easy cleanup**: Delete `.mini_wiki_venv/` to remove everything
- **Portable**: Can move the entire directory to another machine

---

## OS-Specific Details

### Linux

**Requirements**:
- Python 3.9+ with venv module
- Write permissions in working directory

**Installation**:
```bash
./mini_wiki.sh
```

**Virtual Environment Path**:
```
.mini_wiki_venv/bin/python
.mini_wiki_venv/bin/pip
```

### macOS

**Requirements**:
- Python 3.9+ (install via Homebrew if needed)
- Write permissions in working directory

**Installation**:
```bash
./mini_wiki.sh
```

**Virtual Environment Path**:
```
.mini_wiki_venv/bin/python
.mini_wiki_venv/bin/pip
```

**Note**: If using Python from Homebrew:
```bash
brew install python@3.11
/usr/local/bin/python3.11 run.py
```

### Windows

**Requirements**:
- Python 3.9+ (install from python.org or Microsoft Store)
- Write permissions in working directory

**Installation**:
```cmd
mini_wiki.bat
```

**Virtual Environment Path**:
```
.mini_wiki_venv\Scripts\python.exe
.mini_wiki_venv\Scripts\pip.exe
```

**Note**: If Python is not in PATH:
```cmd
C:\Python311\python.exe run.py
```

---

## Troubleshooting

### Issue: "Python is not installed"

**Solution**: Install Python 3.9 or later
- **Linux**: `sudo apt-get install python3.9`
- **macOS**: `brew install python@3.9`
- **Windows**: Download from [python.org](https://www.python.org)

### Issue: "venv module is not available"

**Solution**: Install Python with venv support
- **Linux**: `sudo apt-get install python3.9-venv`
- **macOS**: Usually included with Homebrew Python
- **Windows**: Check "Install pip" during Python installation

### Issue: "Permission denied" (Linux/macOS)

**Solution**: Make script executable
```bash
chmod +x mini_wiki.sh
```

### Issue: "Virtual environment creation failed"

**Solution**: Check write permissions
```bash
# Check if directory is writable
touch mini_wiki/test_write.txt
rm mini_wiki/test_write.txt

# If not writable, change permissions
chmod u+w mini_wiki/
```

### Issue: "Package installation failed"

**Solution**: Check internet connection and try again
```bash
# Remove incomplete venv and retry
rm -rf mini_wiki/.mini_wiki_venv
./mini_wiki.sh
```

### Issue: "Import error after bootstrap"

**Solution**: Verify installation manually
```bash
# Activate venv manually
source mini_wiki/.mini_wiki_venv/bin/activate  # Linux/macOS
# or
mini_wiki\.mini_wiki_venv\Scripts\activate.bat  # Windows

# Test imports
python -c "import numpy; print(numpy.__version__)"
```

---

## Advanced Usage

### Custom Working Directory

```bash
# Run from any directory
cd /path/to/custom/directory
python /path/to/mini_wiki/run.py
```

The virtual environment will be created in the current directory.

### Reusing Existing Virtual Environment

If you already have a virtual environment set up:

```bash
# Activate your venv
source /path/to/venv/bin/activate

# Run mini_wiki
python mini_wiki/run.py
```

### Manual Package Installation

If bootstrap fails, install packages manually:

```bash
# Activate venv
source mini_wiki/.mini_wiki_venv/bin/activate

# Install packages
pip install -r mini_wiki/requirements.txt

# Run mini_wiki
python mini_wiki/run.py
```

### Checking Virtual Environment Status

```bash
# Check if venv exists
ls -la mini_wiki/.mini_wiki_venv

# Check installed packages
source mini_wiki/.mini_wiki_venv/bin/activate
pip list

# Check Python version in venv
python --version
```

---

## Environment Variables

### MINI_WIKI_VENV

Override virtual environment location:

```bash
export MINI_WIKI_VENV=/custom/path/to/venv
python run.py
```

### MINI_WIKI_CONFIG

Override configuration file location:

```bash
export MINI_WIKI_CONFIG=/custom/path/to/config.yaml
python run.py
```

---

## Cleanup

### Remove Virtual Environment

```bash
# Linux/macOS
rm -rf mini_wiki/.mini_wiki_venv

# Windows
rmdir /s /q mini_wiki\.mini_wiki_venv
```

### Remove All mini_wiki Data

```bash
# Linux/macOS
rm -rf mini_wiki/

# Windows
rmdir /s /q mini_wiki
```

---

## Security Considerations

### Virtual Environment Security

- ✅ Isolated from system Python
- ✅ No system-wide package pollution
- ✅ Easy to audit installed packages
- ✅ Can be deleted without affecting system

### Package Verification

The bootstrap system verifies critical packages:

```python
critical_packages = [
    "numpy",
    "pandas",
    "faiss",
    "sentence_transformers",
    "click",
    "yaml",
]
```

### Dependency Pinning

All package versions are pinned in `requirements.txt` for reproducibility:

```
numpy==1.21.0
pandas==1.3.0
faiss-cpu==1.7.0
sentence-transformers==2.2.0
```

---

## Performance Notes

### First Run

- **Time**: 2-5 minutes (depending on internet speed and system)
- **Disk Space**: ~500MB for virtual environment and packages
- **Network**: Downloads ~300MB of packages

### Subsequent Runs

- **Time**: < 1 second (venv already exists)
- **Disk Space**: No additional space
- **Network**: No downloads

---

## Multi-Device Setup

### Moving mini_wiki to Another Device

1. **Copy the entire directory**:
   ```bash
   cp -r mini_wiki /path/to/new/device/
   ```

2. **Run on new device**:
   ```bash
   cd /path/to/new/device/mini_wiki
   ./mini_wiki.sh  # or mini_wiki.bat on Windows
   ```

3. **Bootstrap will**:
   - Detect the new OS
   - Create a new virtual environment
   - Install packages for the new OS
   - Verify installation

### Sharing Configuration

After first run, share configuration:

```bash
# Copy configuration to new device
cp mini_wiki/config/mini_wiki_config.yaml /path/to/new/device/mini_wiki/config/
```

---

## Getting Help

### Check Bootstrap Logs

Bootstrap output is displayed in the terminal. For detailed debugging:

```bash
# Run with verbose output
python run.py --debug
```

### Verify System Requirements

```bash
python -c "
import sys
import platform
print(f'Python: {sys.version}')
print(f'OS: {platform.system()} {platform.release()}')
print(f'Architecture: {platform.machine()}')
"
```

### Report Issues

If you encounter issues:

1. Check the troubleshooting section above
2. Verify system requirements
3. Check internet connection
4. Try removing `.mini_wiki_venv` and running again
5. Report the error message and system information

---

## Next Steps

After successful installation:

1. **Load your first dataset**:
   ```bash
   mini_wiki load path/to/data.csv
   ```

2. **Set your research topic**:
   ```bash
   mini_wiki topic "Your research topic"
   ```

3. **Rank content**:
   ```bash
   mini_wiki rank --limit 20
   ```

4. **Export results**:
   ```bash
   mini_wiki export csv output.csv
   ```

5. **Launch interactive TUI**:
   ```bash
   mini_wiki tui
   ```

---

## Additional Resources

- [Python Installation Guide](https://www.python.org/downloads/)
- [Virtual Environments Documentation](https://docs.python.org/3/tutorial/venv.html)
- [mini_wiki Documentation](README.md)
- [Architecture Guide](../ARCHITECTURE.md)

---

**mini_wiki** - Learn. Teach. Analyze. 🚀
