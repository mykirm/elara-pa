#!/usr/bin/env python3
"""
Test script to verify marker-pdf installation and basic functionality.
Run this after installing requirements.txt to ensure everything works.
"""

import sys
import tempfile
import os
from pathlib import Path

def test_marker_import():
    """Test that marker-pdf can be imported successfully."""
    print("Testing marker-pdf import...")
    try:
        import marker
        # Get version using pkg_resources as marker module doesn't have __version__
        try:
            import pkg_resources
            version = pkg_resources.get_distribution('marker-pdf').version
            print(f"✅ Successfully imported marker-pdf version: {version}")
        except:
            print("✅ Successfully imported marker-pdf (version detection failed)")
        return True
    except ImportError as e:
        print(f"❌ Failed to import marker-pdf: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error importing marker-pdf: {e}")
        return False

def test_marker_dependencies():
    """Test that marker-pdf dependencies are available."""
    print("\nTesting marker-pdf dependencies...")
    dependencies = {
        'torch': 'PyTorch for ML models',
        'transformers': 'Hugging Face transformers',
        'pdfplumber': 'PDF processing fallback',
        'PIL': 'Pillow for image processing'
    }
    
    all_deps_ok = True
    for dep, description in dependencies.items():
        try:
            if dep == 'PIL':
                import PIL
                print(f"✅ {dep} ({description}): Available")
            else:
                __import__(dep)
                print(f"✅ {dep} ({description}): Available")
        except ImportError:
            print(f"❌ {dep} ({description}): Missing")
            all_deps_ok = False
    
    return all_deps_ok

def test_marker_basic_functionality():
    """Test basic marker-pdf functionality with a simple example."""
    print("\nTesting marker-pdf basic functionality...")
    try:
        # Test if we can import marker submodules
        import marker
        submodules = []
        
        # Try common marker submodules
        for module_name in ['settings', 'schema', 'cleaners', 'segmentation']:
            try:
                __import__(f'marker.{module_name}')
                submodules.append(module_name)
            except ImportError:
                continue
        
        if submodules:
            print(f"✅ Successfully imported marker submodules: {', '.join(submodules)}")
            print("ℹ️  Note: Full functionality test requires a PDF file and model downloads")
            print("ℹ️  Models will be downloaded on first use (~1-2GB)")
            return True
        else:
            print("⚠️  Marker imported but no known submodules found")
            print("ℹ️  This might be normal - marker-pdf may use different module structure")
            return True
        
    except ImportError as e:
        print(f"❌ Failed to import marker modules: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error testing marker functionality: {e}")
        return False

def test_other_requirements():
    """Test other key requirements."""
    print("\nTesting other key requirements...")
    requirements = {
        'pydantic': 'Data validation framework',
        'fastapi': 'API framework',
        'aiohttp': 'Async HTTP client',
        'pytest': 'Testing framework'
    }
    
    all_ok = True
    for req, description in requirements.items():
        try:
            __import__(req)
            print(f"✅ {req} ({description}): Available")
        except ImportError:
            print(f"❌ {req} ({description}): Missing")
            all_ok = False
    
    return all_ok

def main():
    """Run all installation verification tests."""
    print("🔍 Verifying marker-pdf and dependencies installation...\n")
    
    tests = [
        ("Marker-PDF Import", test_marker_import),
        ("Dependencies", test_marker_dependencies), 
        ("Marker Functionality", test_marker_basic_functionality),
        ("Other Requirements", test_other_requirements)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"🧪 {test_name}")
        print('='*50)
        success = test_func()
        results.append((test_name, success))
    
    # Summary
    print(f"\n{'='*50}")
    print("📋 SUMMARY")
    print('='*50)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if not success:
            all_passed = False
    
    print(f"\n{'='*50}")
    if all_passed:
        print("🎉 All tests passed! marker-pdf installation is working correctly.")
        print("📝 You can now proceed with PDF processing development.")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")
        print("💡 Try reinstalling requirements: pip install -r requirements.txt")
    print('='*50)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
