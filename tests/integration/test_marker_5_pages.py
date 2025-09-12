#!/usr/bin/env python3
"""Test marker with first 5 pages of UHC PDF for faster verification."""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add marker_env to path
sys.path.insert(0, '/Users/myrakirmani/Desktop/PA/pa-hypergraph-system/marker_env/lib/python3.11/site-packages')

def test_marker_5_pages():
    """Test marker with just the first 5 pages for speed."""
    
    print("🔍 Testing marker with first 5 pages...")
    
    try:
        from marker.scripts.convert_single import convert_single_cli
        
        # Create output directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = f"data/raw/marker_5pages_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save original sys.argv
        original_argv = sys.argv.copy()
        
        try:
            # Set arguments for marker - first 5 pages only
            sys.argv = [
                'convert_single',
                'data/UHC-Commercial-PA-Requirements-2025.pdf',
                '--output_dir', output_dir,
                '--output_format', 'markdown',
                '--page_range', '0-4',  # Pages 0-4 (first 5 pages)
                '--disable_multiprocessing'
            ]
            
            print(f"📄 Converting first 5 pages to: {output_dir}")
            print("⏳ Processing...")
            
            # Run marker conversion
            convert_single_cli()
            
            # Check output
            output_files = list(Path(output_dir).glob("*.md"))
            if output_files:
                markdown_file = output_files[0]
                with open(markdown_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                print(f"✅ Marker conversion successful!")
                print(f"   Output: {markdown_file}")
                print(f"   Size: {len(content):,} characters")
                print(f"   Lines: {len(content.splitlines()):,}")
                
                # Show preview
                print(f"\n📄 Preview (first 500 chars):")
                print("─" * 50)
                preview = content[:500].replace('\n', '\n   ')
                print(f"   {preview}...")
                
                # Show structure info
                lines = content.split('\n')
                headers = [line for line in lines if line.startswith('#')]
                tables = [line for line in lines if '|' in line and len(line.split('|')) > 2]
                
                print(f"\n📊 Content Analysis:")
                print(f"   Headers found: {len(headers)}")
                print(f"   Table rows: {len(tables)}")
                print(f"   Empty lines: {sum(1 for line in lines if not line.strip())}")
                
                if headers:
                    print(f"   Sample headers: {headers[:3]}")
                
                return True
            else:
                print("❌ No output file generated")
                return False
                
        finally:
            # Restore original sys.argv
            sys.argv = original_argv
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_marker_5_pages()
    
    if success:
        print("\n🎉 Success! Marker is working correctly with high-quality extraction.")
        print("💡 Ready to process full documents or integrate with rule parsing.")
    else:
        print("\n❌ Test failed. Check error messages above.")