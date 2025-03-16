"""Setup script for recruitx package."""

from setuptools import setup, find_packages

setup(
    name="recruitx",
    version="0.1.0",
    description="Zero-budget, AGI-level recruitment matching system",
    author="Shristyverse LLC",
    author_email="contact@shristyverse.com",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
        "joblib>=1.3.0",
        "google-cloud-aiplatform>=1.35.0",
        "google-generativeai>=0.3.0",
        "pandas>=2.1.0",
        "scipy>=1.11.0",
        "torch>=2.1.0",
        "transformers>=4.35.0",
        "streamlit>=1.32.0",
        "streamlit-extras>=0.4.0",
        "streamlit-option-menu>=0.3.6",
        "plotly>=5.19.0",
        "altair>=5.2.0",
        "opencv-python>=4.9.0",
        "pytest>=8.0.0",
        "pytest-asyncio>=0.23.0",
        "pytest-xdist>=3.5.0",
        "psutil>=5.9.0",
        "memory-profiler>=0.61.0",
        "rich>=13.7.0",
        "jinja2>=3.1.0",
    ],
    python_requires=">=3.12",
) 