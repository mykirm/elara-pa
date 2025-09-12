#!/usr/bin/env python3
"""Test script for UHC PDF extraction only (no rule parsing).

This script tests:
1. PDF to Markdown conversion using marker-pdf
2. Table extraction using pdfplumber 
3. Shows output files and locations
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add marker_env to path
sys.path.insert(0, '/Users/myrakirmani/Desktop/PA/pa-hypergraph-system/marker_env/lib/python3.11/site-packages')

from src.parsers import (
    convert_pdf_to_markdown,
    extract_tables_with_pdfplumber
)


def test_extraction_only():
    """Test only the extraction functions without rule parsing."""
    
    pdf_path = "data/UHC-Commercial-PA-Requirements-2025.pdf"
    
    print("=" * 80)
    print("UHC PDF Extraction Test (No Rule Parsing)")
    print("=" * 80)
    print(f"PDF: {pdf_path}")
    print(f"Start: {datetime.now().isoformat()}")
    print()
    
    # Check PDF exists
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    print(f"✅ PDF found: {Path(pdf_path).stat().st_size / 1024:.1f} KB")
    
    # Test 1: PDF to Markdown conversion
    print("\n" + "-" * 50)
    print("Test 1: PDF to Markdown Conversion")
    print("-" * 50)
    
    try:
        markdown_text = convert_pdf_to_markdown(pdf_path)
        
        print(f"✅ Conversion successful")
        print(f"   Markdown length: {len(markdown_text):,} characters")
        print(f"   Line count: {len(markdown_text.splitlines()):,}")
        
        # Show first 1000 chars as preview
        print(f"\n   📄 Preview (first 1000 chars):")
        print("   " + "─" * 47)
        preview = markdown_text[:1000].replace('\n', '\n   ')
        print(f"   {preview}...")
        
        # Show where raw output was saved
        raw_files = list(Path("data/raw").glob("*.md"))
        if raw_files:
            latest_raw = max(raw_files, key=os.path.getctime)
            print(f"\n   💾 Raw markdown saved to: {latest_raw}")
        
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        return
    
    # Test 2: Table extraction
    print("\n" + "-" * 50) 
    print("Test 2: Table Extraction with pdfplumber")
    print("-" * 50)
    
    try:
        tables = extract_tables_with_pdfplumber(pdf_path)
        
        print(f"✅ Table extraction completed")
        print(f"   Tables found: {len(tables)}")
        
        if tables:
            # Show details of first few tables
            for i, table in enumerate(tables[:3]):
                print(f"\n   📊 Table {i+1} (Page {table['page']}):")
                print(f"       Headers: {table['headers'][:3]}{'...' if len(table['headers']) > 3 else ''}")
                print(f"       Rows: {len(table['rows'])}")
                print(f"       Columns: {len(table['headers'])}")
            
            if len(tables) > 3:
                print(f"   ... and {len(tables) - 3} more tables")
            
            # Show where table data was saved
            table_files = list(Path("data/raw").glob("*_tables.json"))
            if table_files:
                latest_table = max(table_files, key=os.path.getctime)
                print(f"\n   💾 Table data saved to: {latest_table}")
        else:
            print("   ℹ️  No tables found in PDF")
        
    except Exception as e:
        print(f"❌ Table extraction failed: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("Extraction Test Summary")
    print("=" * 80)
    
    print(f"Input:")
    print(f"  📄 PDF: {pdf_path} ({Path(pdf_path).stat().st_size / 1024:.1f} KB)")
    
    print(f"\nOutput files created:")
    
    # List all files in data/raw/
    raw_dir = Path("data/raw")
    if raw_dir.exists():
        raw_files = list(raw_dir.glob("*"))
        raw_files.sort(key=os.path.getctime, reverse=True)  # Most recent first
        
        for file in raw_files:
            size_kb = file.stat().st_size / 1024
            mod_time = datetime.fromtimestamp(file.stat().st_mtime).strftime('%H:%M:%S')
            print(f"  📁 {file.name} ({size_kb:.1f} KB, {mod_time})")
    
    print(f"\nNext steps:")
    print(f"  1. Review the markdown output for structure and content")
    print(f"  2. Check table extraction for tabular data")  
    print(f"  3. When ready, test rule parsing with parse_markdown_to_rules()")
    
    print(f"\nTest completed: {datetime.now().isoformat()}")


if __name__ == "__main__":
