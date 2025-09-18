#!/usr/bin/env python3
"""Test enhanced parser features via API endpoints"""

import requests
import json

def test_enhanced_upload():
    """Test the enhanced upload endpoint with a sample document"""
    
    # Sample markdown content with enhanced patterns
    sample_markdown = """
# Cardiovascular Procedures

Prior authorization is required for patients ages 18 and older when requesting 
service in an outpatient hospital setting. Prior authorization not required if 
performed in an office setting.

Prior authorization not required for the following diagnosis codes:
I25.110 I25.111 I25.118 I25.119

Geographic exceptions: Prior authorization required for all states except in
Alaska, Massachusetts, Texas, Utah, and Wisconsin.

CPT Codes: 33776 33777 33778 33779
"""
    
    # Create a temporary markdown file
    with open("/tmp/test_enhanced.md", "w") as f:
        f.write(sample_markdown)
    
    # Test enhanced upload endpoint
    print("🚀 Testing Enhanced Upload Endpoint")
    
    try:
        with open("/tmp/test_enhanced.md", "rb") as f:
            # Create a fake PDF file for testing
            files = {"file": ("test_enhanced.pdf", f, "application/pdf")}
            
            # This will fail because it's not a real PDF, but let's see what happens
            response = requests.post("http://localhost:8000/upload-pdf-enhanced", files=files)
            
        print(f"Response status: {response.status_code}")
        if response.status_code == 422:
            print("Expected validation error for non-PDF file")
        else:
            print(f"Response: {response.json()}")
            
    except Exception as e:
        print(f"Error testing enhanced upload: {e}")

def test_migration_commands():
    """Test migration commands and configuration"""
    
    print("\n🔧 Testing Migration Commands")
    
    # Test capabilities endpoint
    try:
        response = requests.get("http://localhost:8000/capabilities")
        capabilities = response.json()
        
        print("Current System Capabilities:")
        print(f"  Parser Mode: {'Enhanced' if capabilities['system_capabilities']['enhanced_parser_enabled'] else 'Original'}")
        print(f"  Rules Loaded: {capabilities['rules_loaded']}")
        print(f"  Rule Type: {capabilities['rule_type']}")
        print(f"  Enhanced Features Available: {sum(capabilities['enhanced_features'].values())}")
        
        print("\nAvailable Endpoints:")
        for name, endpoint in capabilities['available_endpoints'].items():
            print(f"  {name}: {endpoint}")
            
    except Exception as e:
        print(f"Error testing capabilities: {e}")

def test_smart_evaluation():
    """Test the smart evaluation endpoint"""
    
    print("\n🧠 Testing Smart Evaluation")
    
    test_cases = [
        {
            "name": "Office Setting (should not require auth)",
            "data": {
                "cpt_codes": ["33776"],
                "patient_age": 45,
                "place_of_service": "11",  # Office
                "state": "CA"
            }
        },
        {
            "name": "Outpatient Hospital (should require auth)",
            "data": {
                "cpt_codes": ["33776"],
                "patient_age": 45,
                "place_of_service": "22",  # Outpatient Hospital
                "state": "CA"
            }
        },
        {
            "name": "Excluded State (should not require auth)",
            "data": {
                "cpt_codes": ["33776"],
                "patient_age": 45,
                "place_of_service": "22",
                "state": "TX"  # Excluded state
            }
        }
    ]
    
    for test_case in test_cases:
        try:
            response = requests.post(
                "http://localhost:8000/authorization/evaluate-smart",
                json=test_case["data"],
                headers={"Content-Type": "application/json"}
            )
            
            result = response.json()
            print(f"\n{test_case['name']}:")
            print(f"  Authorization Required: {result['requires_authorization']}")
            print(f"  Reason: {result['primary_reason']}")
            print(f"  Method: {result['evaluation_method']}")
            print(f"  Confidence: {result['confidence_score']}")
            
        except Exception as e:
            print(f"Error in test case '{test_case['name']}': {e}")

if __name__ == "__main__":
    print("🎯 Enhanced Parser Migration Test Suite")
    print("=" * 50)
    
    test_migration_commands()
    test_smart_evaluation()
    # Note: Enhanced upload test disabled as it requires actual PDF processing
    
    print("\n" + "=" * 50)
    print("✅ Migration testing complete!")
    print("\nTo enable enhanced parser mode:")
    print("  export USE_ENHANCED_PARSER=true")
    print("  python3 scripts/run_server.py")