#!/usr/bin/env python3
"""Quick test to see if marker models are ready and working."""

import sys
import os
from pathlib import Path

# Add marker_env to path
sys.path.insert(0, '/Users/myrakirmani/Desktop/PA/pa-hypergraph-system/marker_env/lib/python3.11/site-packages')

def quick_marker_test():
    """Test if marker is ready to use."""
    
    print("🔍 Testing marker readiness...")
    
    try:
        from marker.scripts.convert_single import convert_single_cli
        print("✅ Marker import successful")
        
        # Check if models directory exists and has content
        model_dirs = [
            Path.home() / "Library/Caches/datalab/models",
            Path.home() / ".cache/huggingface/transformers"  # Alternative location
        ]
        
        total_size = 0
        for model_dir in model_dirs:
            if model_dir.exists():
                size = sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file())
                total_size += size
                print(f"📁 {model_dir}: {size / 1024**3:.1f} GB")
        
        print(f"📊 Total model size: {total_size / 1024**3:.1f} GB")
        
        # Try a very quick marker test
        if total_size > 100 * 1024**2:  # More than 100MB suggests models are downloading
            print("🚀 Models appear to be downloaded, testing conversion...")
            
            # Set up minimal test
            sys.argv = [
                'convert_single',
                'data/UHC-Commercial-PA-Requirements-2025.pdf',
                '--output_dir', 'data/raw/marker_quick_test',
                '--output_format', 'markdown',
                '--disable_multiprocessing',
                '--page_range', '0'  # Just first page for quick test
            ]
            
            os.makedirs('data/raw/marker_quick_test', exist_ok=True)
            
            print("   Testing first page conversion...")
            convert_single_cli()
            
            # Check output
            output_files = list(Path('data/raw/marker_quick_test').glob('*.md'))
            if output_files:
                with open(output_files[0], 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"✅ Quick test successful! Generated {len(content):,} characters")
                print(f"   Preview: {content[:200]}...")
                return True
            else:
                print("❌ No output file generated")
                return False
        else:
            print("⏳ Models still downloading (less than 100MB found)")
            return False
            
    except Exception as e:
        print(f"❌ Marker test failed: {e}")
        return False


if __name__ == "__main__":
    success = quick_marker_test()
    
    if success:
        print("\n🎉 Marker is ready! You can now run full conversion tests.")
        print("   Estimated model space: 1-3 GB total")
        print("   Next: python test_extraction_only.py")
    else:
        print("\n⏳ Marker not ready yet. Models may still be downloading.")
        print("   Typical download: ~1.3GB text recognition model + others")
        print("   This can take 5-15 minutes depending on connection speed.")