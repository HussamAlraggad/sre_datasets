"""
Setup script for mini_wiki
"""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mini_wiki",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Universal research assistant with hybrid ranking and AI teaching",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-repo/mini_wiki",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.21.0",
        "scipy>=1.7.0",
        "pandas>=1.3.0",
        "faiss-cpu>=1.7.0",
        "sentence-transformers>=2.2.0",
        "scikit-learn>=1.0.0",
        "pyyaml>=6.0",
        "pydantic>=1.9.0",
        "click>=8.0.0",
        "rich>=10.0.0",
        "textual>=0.1.0",
        "python-dotenv>=0.19.0",
        "PyPDF2>=1.26.0",
        "requests>=2.27.0",
        "beautifulsoup4>=4.10.0",
        "lxml>=4.9.0",
        "openpyxl>=3.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "pytest-asyncio>=0.18.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "isort>=5.10.0",
            "mypy>=0.950",
            "pre-commit>=2.17.0",
        ],
        "gpu": [
            "faiss-gpu>=1.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mini_wiki=mini_wiki.main:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
