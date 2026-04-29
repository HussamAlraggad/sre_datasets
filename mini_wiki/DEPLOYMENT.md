"""
mini_wiki Deployment Guide
Complete deployment instructions for production and development environments

Contents:
- System Requirements
- Installation Methods
- Configuration
- Environment Setup
- Running the Application
- Monitoring and Maintenance
- Troubleshooting
"""

# ============================================================================
# MINI_WIKI DEPLOYMENT GUIDE
# ============================================================================

## System Requirements

### Minimum Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.9+ | 3.11+ |
| RAM | 2 GB | 4 GB+ |
| Disk Space | 1 GB | 5 GB+ |
| CPU | 1 core | 2+ cores |
| OS | Linux/macOS/Windows | Linux (Ubuntu 22.04+) |

### Python Dependencies

```
numpy>=1.21.0
pandas>=1.3.0
faiss-cpu>=1.7.0
sentence-transformers>=2.2.0
scikit-learn>=1.0.0
click>=8.0.0
pyyaml>=6.0
pydantic>=2.0.0
```

### Optional Dependencies

```
textual>=0.40.0        # Enhanced TUI
rich>=13.0.0           # Rich console output
reportlab>=4.0.0       # PDF export
```

## Installation Methods

### Method 1: Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/user/mini_wiki.git
cd mini_wiki

# Run the bootstrap installer
python3 bootstrap.py

# The bootstrap system will:
# 1. Detect your OS
# 2. Create virtual environment
# 3. Install all dependencies
# 4. Verify installation
# 5. Launch the application
```

### Method 2: Manual Install

```bash
# Clone the repository
git clone https://github.com/user/mini_wiki.git
cd mini_wiki

# Create virtual environment
python3 -m venv .mini_wiki_venv

# Activate virtual environment
# Linux/macOS:
source .mini_wiki_venv/bin/activate
# Windows:
# .mini_wiki_venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python3 -c "import mini_wiki; print('mini_wiki installed successfully')"
```

### Method 3: System-Wide Install

```bash
# Run the system installer
python3 install.py

# This will:
# 1. Install mini_wiki to system Python
# 2. Create launcher scripts
# 3. Add to PATH
# 4. Create default configuration

# After installation, run from anywhere:
mini_wiki --help
```

### Method 4: Docker Install

```bash
# Build Docker image
docker build -t mini_wiki .

# Run container
docker run -it --rm \
  -v ./data:/app/data \
  -v ./config:/app/config \
  mini_wiki

# Run with custom configuration
docker run -it --rm \
  -v ./data:/app/data \
  -v ./config:/app/config \
  -e MINI_WIKI_THEME=light \
  mini_wiki
```

## Configuration

### Configuration File

Create `~/.mini_wiki/config.yaml`:

```yaml
# Data paths
data_path: ./data
index_path: ./index
storage_path: ./storage

# Display settings
theme: dark
max_results: 100

# Performance settings
enable_caching: true
cache_size_mb: 100
batch_size: 32

# Embedding settings
embedding_model: all-MiniLM-L6-v2
embedding_device: cpu

# Ranking settings
relevance_weight: 0.6
importance_weight: 0.4

# Search settings
default_limit: 10
min_relevance: 0.3

# Export settings
default_export_format: markdown
export_include_metadata: true
export_include_scores: true
export_include_references: true

# Logging settings
log_level: INFO
log_file: ~/.mini_wiki/mini_wiki.log
```

### Environment Variables

```bash
# Data paths
export MINI_WIKI_DATA_PATH=/path/to/data
export MINI_WIKI_INDEX_PATH=/path/to/index
export MINI_WIKI_STORAGE_PATH=/path/to/storage

# Display settings
export MINI_WIKI_THEME=dark
export MINI_WIKI_MAX_RESULTS=100

# Performance settings
export MINI_WIKI_ENABLE_CACHING=true
export MINI_WIKI_CACHE_SIZE_MB=100

# Embedding settings
export MINI_WIKI_EMBEDDING_MODEL=all-MiniLM-L6-v2
export MINI_WIKI_EMBEDDING_DEVICE=cpu

# Logging settings
export MINI_WIKI_LOG_LEVEL=INFO
export MINI_WIKI_LOG_FILE=~/.mini_wiki/mini_wiki.log
```

### Configuration Priority

1. Command-line arguments (highest)
2. Environment variables
3. Project config (`./mini_wiki_config.yaml`)
4. User config (`~/.mini_wiki/config.yaml`)
5. System config (`/etc/mini_wiki/config.yaml`)
6. Default values (lowest)

## Running the Application

### Command-Line Interface

```bash
# Show help
mini_wiki --help

# Load data
mini_wiki load --source data.csv --format csv

# Search
mini_wiki search --query "machine learning" --limit 10

# Rank results
mini_wiki rank --query "python" --preset balanced

# Export results
mini_wiki export --format markdown --output results.md

# Launch TUI
mini_wiki tui

# Show configuration
mini_wiki show --config
```

### Python API

```python
from mini_wiki.integrated_system import create_system, SystemConfig

# Create system with defaults
system = create_system()

# Or with custom configuration
config = SystemConfig(
    data_path="./data",
    theme="dark",
    max_results=100,
)
system = create_system(config)

# Load data
system.load_data("documents.csv", "csv")

# Search
results = system.search("machine learning", limit=10)

# Export
system.export_results(results, "markdown", "results.md")

# Get statistics
stats = system.get_statistics()
print(f"Total searches: {stats['total_searches']}")

# Shutdown
system.shutdown()
```

### TUI Mode

```bash
# Launch interactive TUI
mini_wiki tui

# With custom theme
mini_wiki tui --theme light

# With custom dimensions
mini_wiki tui --width 120 --height 40
```

## Monitoring and Maintenance

### Health Check

```python
# Check system health
health = system.health_check()
print(f"Status: {health['status']}")
print(f"Components: {health['components']}")
```

### Performance Monitoring

```python
# Get system statistics
stats = system.get_statistics()
print(f"Total documents: {stats['total_documents']}")
print(f"Total searches: {stats['total_searches']}")
print(f"Average search time: {stats['search_time_ms']:.2f}ms")
```

### Cache Management

```python
# Optimize performance (clears cache)
system.optimize_performance()

# Check cache status
print(f"Cache entries: {len(system.cache)}")
```

### Log Management

```bash
# View logs
tail -f ~/.mini_wiki/mini_wiki.log

# Clear logs
> ~/.mini_wiki/mini_wiki.log

# Set log level
export MINI_WIKI_LOG_LEVEL=DEBUG
```

### Backup and Restore

```bash
# Backup data
cp -r ./data ./data_backup
cp -r ./index ./index_backup
cp -r ./storage ./storage_backup

# Restore data
cp -r ./data_backup ./data
cp -r ./index_backup ./index
cp -r ./storage_backup ./storage
```

## Troubleshooting

### Common Issues

#### 1. Installation Fails

```bash
# Check Python version
python3 --version  # Should be 3.9+

# Check pip
python3 -m pip --version

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

#### 2. Out of Memory

```bash
# Reduce batch size in config
batch_size: 16  # Default is 32

# Reduce cache size
cache_size_mb: 50  # Default is 100

# Use CPU instead of GPU
embedding_device: cpu
```

#### 3. Slow Search

```bash
# Enable caching
enable_caching: true

# Reduce max results
max_results: 50  # Default is 100

# Optimize index
mini_wiki optimize
```

#### 4. Export Fails

```bash
# Check output path permissions
ls -la /path/to/output

# Check disk space
df -h

# Try different format
mini_wiki export --format json --output results.json
```

### Debug Mode

```bash
# Enable debug logging
export MINI_WIKI_LOG_LEVEL=DEBUG

# Run with verbose output
mini_wiki --verbose search --query "test"
```

### Getting Help

- **Documentation**: https://mini_wiki.readthedocs.io
- **GitHub Issues**: https://github.com/user/mini_wiki/issues
- **Email**: support@mini_wiki.dev
- **Discord**: https://discord.gg/mini_wiki

## Security Considerations

### Data Security

- Store sensitive data in encrypted directories
- Use environment variables for API keys
- Enable logging for audit trails
- Regularly backup data

### Network Security

- Use HTTPS for URL loading
- Validate all input data
- Sanitize exported content
- Restrict file system access

### Access Control

- Set appropriate file permissions
- Use virtual environments
- Keep dependencies updated
- Review security advisories

## Performance Tuning

### Index Optimization

```yaml
# Use HNSW index for large datasets
index_type: hnsw
hnsw_m: 32
hnsw_ef_construction: 200
```

### Embedding Optimization

```yaml
# Use GPU if available
embedding_device: cuda

# Use smaller model for faster inference
embedding_model: all-MiniLM-L6-v2

# Increase batch size for GPU
batch_size: 64
```

### Cache Optimization

```yaml
# Enable caching
enable_caching: true

# Set cache size
cache_size_mb: 200

# Cache embeddings
cache_embeddings: true
```

## Scaling

### Vertical Scaling

- Increase RAM for larger datasets
- Use GPU for faster embeddings
- Use SSD for faster I/O

### Horizontal Scaling

- Distribute data across multiple instances
- Use load balancer for search requests
- Share index across instances

### Cloud Deployment

```bash
# Deploy to AWS
aws ec2 run-instances --image-id ami-xxx --instance-type t3.large

# Deploy to GCP
gcloud compute instances create mini-wiki --machine-type=n2-standard-4

# Deploy to Azure
az vm create --name mini-wiki --size Standard_D4s_v3
```