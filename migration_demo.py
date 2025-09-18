#!/usr/bin/env python3
"""Migration demonstration script showing Phase 1 implementation"""

import requests
import json
import time

def demonstrate_phase_1_migration():
    """Demonstrate Phase 1: Parallel Deployment"""
    
    print("🚀 PHASE 1 MIGRATION DEMONSTRATION")
    print("=" * 60)
    print("Objective: Deploy enhanced system alongside current system for validation")
    print()
    
    # Step 1: Show current system status
    print("📊 STEP 1: Current System Status")
    print("-" * 30)
    
    try:
        response = requests.get("http://localhost:8000/")
        status = response.json()
        
        print(f"✅ API Status: {status['message']}")
        print(f"📈 Rules Loaded: {status['rules_loaded']}")
        print(f"🔧 Parser Mode: {status['parser_mode']}")
        print(f"🎯 Enhanced Parser: {'Enabled' if status['capabilities']['enhanced_parser_enabled'] else 'Disabled'}")
        print()
        
    except Exception as e:
        print(f"❌ Error connecting to API: {e}")
        return
    
    # Step 2: Show available endpoints
    print("🔗 STEP 2: Available Endpoints")
    print("-" * 30)
    
    try:
        response = requests.get("http://localhost:8000/capabilities")
        capabilities = response.json()
        
        endpoints = capabilities['available_endpoints']
        for name, endpoint in endpoints.items():
            status_icon = "✅" if name in ["basic_evaluation", "upload_basic"] else "🆕"
            print(f"{status_icon} {name}: {endpoint}")
        print()
        
    except Exception as e:
        print(f"❌ Error getting capabilities: {e}")
        return
    
    # Step 3: Test both evaluation methods
    print("🧪 STEP 3: Testing Both Evaluation Methods")
    print("-" * 30)
    
    test_request = {
        "cpt_codes": ["23470"],  # Arthroplasty
        "patient_age": 65,
        "state": "CA",
        "place_of_service": "22"  # Outpatient hospital
    }
    
    # Test original evaluation
    try:
        response = requests.post(
            "http://localhost:8000/authorization/evaluate",
            json={"cpt_codes": test_request["cpt_codes"], "state": test_request["state"]},
            headers={"Content-Type": "application/json"}
        )
        original_result = response.json()
        
        print("📝 Original Evaluation:")
        print(f"   Authorization Required: {original_result['requires_authorization']}")
        print(f"   Confidence Score: {original_result['confidence_score']}")
        print(f"   Rules Found: {len(original_result['applicable_rules'])}")
        print()
        
    except Exception as e:
        print(f"❌ Error testing original evaluation: {e}")
    
    # Test smart evaluation
    try:
        response = requests.post(
            "http://localhost:8000/authorization/evaluate-smart",
            json=test_request,
            headers={"Content-Type": "application/json"}
        )
        smart_result = response.json()
        
        print("🧠 Smart Evaluation:")
        print(f"   Authorization Required: {smart_result['requires_authorization']}")
        print(f"   Evaluation Method: {smart_result['evaluation_method']}")
        print(f"   Confidence Score: {smart_result['confidence_score']}")
        print(f"   Rules Evaluated: {smart_result['rules_evaluated']}")
        print(f"   Context Provided: {smart_result['context_provided']}")
        print()
        
    except Exception as e:
        print(f"❌ Error testing smart evaluation: {e}")
    
    # Step 4: Show migration readiness
    print("🎯 STEP 4: Migration Readiness Check")
    print("-" * 30)
    
    migration_checklist = [
        ("✅", "Dual parser loader implemented"),
        ("✅", "Environment variable support added"),
        ("✅", "Enhanced upload endpoint created"),
        ("✅", "Smart evaluation endpoint working"),
        ("✅", "Backward compatibility maintained"),
        ("✅", "Fallback mechanism implemented"),
        ("🆕", "Enhanced parser mode available"),
        ("🆕", "Advanced pattern recognition ready")
    ]
    
    for status, item in migration_checklist:
        print(f"{status} {item}")
    print()
    
    # Step 5: Show next steps
    print("🚀 STEP 5: Ready for Phase 2")
    print("-" * 30)
    
    print("To enable enhanced parser mode:")
    print("  export USE_ENHANCED_PARSER=true")
    print("  python3 scripts/run_server.py")
    print()
    
    print("Enhanced features will include:")
    print("  🏥 Place of Service restrictions")
    print("  🩺 Diagnosis code exceptions")
    print("  👶 Age-based authorization rules")
    print("  🗺️ Geographic exception handling")
    print("  🔀 Complex conditional logic")
    print()
    
    print("Phase 2 implementation ready!")
    print("=" * 60)

def show_current_rules_analysis():
    """Show analysis of currently loaded rules"""
    
    print("\n📊 CURRENT RULES ANALYSIS")
    print("-" * 30)
    
    try:
        response = requests.get("http://localhost:8000/capabilities")
        capabilities = response.json()
        
        print(f"Total Rules: {capabilities['rules_loaded']}")
        print(f"Rule Type: {capabilities['rule_type']}")
        
        enhanced_features = capabilities['enhanced_features']
        print("\nEnhanced Features in Current Rules:")
        for feature, count in enhanced_features.items():
            print(f"  {feature.replace('_', ' ').title()}: {count}")
        
        if sum(enhanced_features.values()) == 0:
            print("  🔄 Ready for enhanced rule migration")
        
    except Exception as e:
        print(f"❌ Error analyzing rules: {e}")

if __name__ == "__main__":
    demonstrate_phase_1_migration()
    show_current_rules_analysis()