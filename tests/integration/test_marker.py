#!/usr/bin/env python3
"""Test script to verify Marker PDF installation and basic functionality."""

import sys
import os

# Ensure we're using the virtual environment
venv_path = '/Users/myrakirmani/Desktop/PA/marker_env'
sys.path.insert(0, f'{venv_path}/lib/python3.11/site-packages')

try:
    # Import marker package
    import marker
    print("✅ Marker package imported")
    
    # Import the converter utilities
    from marker.converters.pdf import PdfConverter
    from marker.settings import Settings
    
    print("✅ Marker PdfConverter and Settings imported successfully")
    print(f"   Marker installation verified in: {venv_path}")
    print("\nTo use Marker in your code:")
    print("1. Activate the environment: source marker_env/bin/activate")
    print("2. Use the converter: from marker.converters.pdf import PdfConverter")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nTrying alternative import paths...")
    
    # Try command-line interface
    import subprocess
    result = subprocess.run(
        [f"{venv_path}/bin/python", "-m", "marker", "--help"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ Marker CLI is available")
        print("   Use: python -m marker <pdf_file>")
    else:
        print("❌ Marker CLI not found")
        print(f"   Error: {result.stderr}")