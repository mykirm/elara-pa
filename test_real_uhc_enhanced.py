#!/usr/bin/env python3
"""Test enhanced parser with real UHC document patterns"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from parsers.payer_rules.uhc_rules import parse_markdown_to_rules
from parsers.payer_rules.uhc_rules_enhanced import parse_markdown_to_enhanced_rules

def test_real_uhc_enhanced():
    """Test enhanced parser with real UHC markdown if available"""
    
    print("🏥 REAL UHC DOCUMENT ENHANCED PARSER TEST")
    print("=" * 60)
    
    # Check if we have the real UHC markdown
    uhc_markdown_path = "data/processed/uhc_2025_test_20250916_092400.md"
    
    if not os.path.exists(uhc_markdown_path):
        print(f"❌ UHC markdown file not found at {uhc_markdown_path}")
        print("Using sample UHC content instead...")
        
        # Use a representative sample from real UHC patterns
        uhc_content = """
# UHC Commercial Prior Authorization Requirements 2025

## Arthroplasty (Joint Replacement)
Arthroplasty Prior authorization required. 23470 23472 23473 23474
24360 24361 24362 24363 24365 24370 24371 25441 25442 25443 25444 25446
25449 27120 27125 27130 27132 27134 27137 27138 27437 27438 27440 27441
27442 27443 27445 27446 27447 27486 27487 27700 27702 27703

## Arthroscopy
Arthroscopy Prior authorization required. Prior authorization is required for all states.
In addition, site of service will be reviewed as part of the prior authorization process for the following codes
except in Alaska, Massachusetts, Puerto Rico, Rhode Island, Texas, Utah, the Virgin Islands and Wisconsin.

29805 29806 29807 29819 29820 29821 29822 29823 29824 29825 29826 29827 29828

## Cardiovascular Procedures
Prior authorization is required for patients ages 18 and older when performed in an outpatient hospital setting.
Prior authorization not required if performed in an office setting.

Prior authorization not required for the following diagnosis codes:
I25.110 I25.111 I25.118 I25.119 I34.0 I34.1 I34.2

33776 33777 33778 33779 33786 33788 33840 33845
"""
    else:
        print(f"✅ Found UHC markdown at {uhc_markdown_path}")
        try:
            with open(uhc_markdown_path, 'r', encoding='utf-8') as f:
                uhc_content = f.read()
            print(f"📄 Loaded {len(uhc_content)} characters of UHC content")
        except Exception as e:
            print(f"❌ Error reading UHC file: {e}")
            return
    
    print("\n🔄 PROCESSING WITH BOTH PARSERS...")
    print("-" * 40)
    
    # Test original parser
    print("📊 ORIGINAL PARSER RESULTS:")
    try:
        original_rules = parse_markdown_to_rules(uhc_content, "UHC_real_test_original.pdf")
        
        # Analyze original results
        total_cpt_codes = set()
        auth_counts = {}
        geographic_rules = 0
        
        for rule in original_rules:
            total_cpt_codes.update(rule.cpt_codes)
            auth_req = str(rule.auth_requirement)
            auth_counts[auth_req] = auth_counts.get(auth_req, 0) + 1
            if rule.excluded_states:
                geographic_rules += 1
        
        print(f"   Rules extracted: {len(original_rules)}")
        print(f"   Unique CPT codes: {len(total_cpt_codes)}")
        print(f"   Authorization breakdown: {auth_counts}")
        print(f"   Rules with geographic exceptions: {geographic_rules}")
        
        # Show sample rules
        print("   📋 Sample rules:")
        for i, rule in enumerate(original_rules[:3]):
            print(f"      {i+1}. {rule.service[:50]}... - {rule.auth_requirement} ({len(rule.cpt_codes)} codes)")
        
    except Exception as e:
        print(f"   ❌ Original parser error: {e}")
        original_rules = []
    
    # Test enhanced parser
    print("\n🚀 ENHANCED PARSER RESULTS:")
    try:
        enhanced_rules = parse_markdown_to_enhanced_rules(uhc_content, "UHC_real_test_enhanced.pdf")
        
        # Analyze enhanced results
        total_cpt_codes = set()
        auth_counts = {}
        enhanced_features = {
            "place_of_service": 0,
            "diagnosis_exceptions": 0,
            "age_restrictions": 0,
            "geographic_exceptions": 0,
            "conditional_logic": 0
        }
        
        dx_codes_count = 0
        excluded_states_count = 0
        
        for rule in enhanced_rules:
            total_cpt_codes.update(rule.cpt_codes)
            auth_req = str(rule.auth_requirement)
            auth_counts[auth_req] = auth_counts.get(auth_req, 0) + 1
            
            # Count enhanced features
            if rule.place_of_service_restrictions:
                enhanced_features["place_of_service"] += 1
            if rule.diagnosis_exceptions:
                enhanced_features["diagnosis_exceptions"] += 1
                for dx_exception in rule.diagnosis_exceptions:
                    dx_codes_count += len(dx_exception.icd_codes)
            if rule.age_restrictions:
                enhanced_features["age_restrictions"] += 1
            if rule.excluded_states or rule.included_states:
                enhanced_features["geographic_exceptions"] += 1
                excluded_states_count += len(rule.excluded_states)
            if rule.conditional_logic:
                enhanced_features["conditional_logic"] += 1
        
        print(f"   Rules extracted: {len(enhanced_rules)}")
        print(f"   Unique CPT codes: {len(total_cpt_codes)}")
        print(f"   Authorization breakdown: {auth_counts}")
        
        print(f"   🎯 Enhanced Features Detected:")
        print(f"      Place of Service rules: {enhanced_features['place_of_service']}")
        print(f"      Diagnosis exceptions: {enhanced_features['diagnosis_exceptions']} ({dx_codes_count} ICD codes)")
        print(f"      Age restrictions: {enhanced_features['age_restrictions']}")
        print(f"      Geographic exceptions: {enhanced_features['geographic_exceptions']} ({excluded_states_count} excluded states)")
        print(f"      Conditional logic: {enhanced_features['conditional_logic']}")
        
        # Show sample enhanced rules
        print("   📋 Sample enhanced rules:")
        for i, rule in enumerate(enhanced_rules[:3]):
            features = []
            if rule.place_of_service_restrictions:
                features.append("POS")
            if rule.diagnosis_exceptions:
                features.append("DX")
            if rule.age_restrictions:
                features.append("Age")
            if rule.excluded_states:
                features.append("Geo")
            feature_str = f" [{', '.join(features)}]" if features else ""
            
            print(f"      {i+1}. {rule.service[:40]}...{feature_str} - {rule.auth_requirement} ({len(rule.cpt_codes)} codes)")
        
        # Test enhanced evaluation
        print("\n🧠 ENHANCED EVALUATION EXAMPLES:")
        print("-" * 30)
        
        # Find a rule with enhanced features to test
        test_rule = None
        for rule in enhanced_rules:
            if rule.place_of_service_restrictions or rule.diagnosis_exceptions or rule.excluded_states:
                test_rule = rule
                break
        
        if test_rule:
            print(f"Testing rule: {test_rule.service[:50]}...")
            
            # Test scenarios
            scenarios = [
                {
                    "name": "Office Setting",
                    "context": {"patient_age": 45, "place_of_service": "11", "patient_state": "CA"}
                },
                {
                    "name": "Outpatient Hospital",
                    "context": {"patient_age": 45, "place_of_service": "22", "patient_state": "CA"}
                },
                {
                    "name": "Excluded State",
                    "context": {"patient_age": 45, "place_of_service": "22", "patient_state": "TX"}
                }
            ]
            
            for scenario in scenarios:
                try:
                    evaluation = test_rule.evaluate_authorization(**scenario["context"])
                    print(f"   {scenario['name']}: {evaluation['reason']} (Auth: {evaluation['auth_required']}, Confidence: {evaluation['confidence']})")
                except Exception as e:
                    print(f"   {scenario['name']}: Evaluation error - {e}")
        
    except Exception as e:
        print(f"   ❌ Enhanced parser error: {e}")
        enhanced_rules = []
    
    # Comparison summary
    print(f"\n📊 COMPARISON SUMMARY")
    print("=" * 60)
    
    if original_rules and enhanced_rules:
        original_cpt_count = len(set(code for rule in original_rules for code in rule.cpt_codes))
        enhanced_cpt_count = len(set(code for rule in enhanced_rules for code in rule.cpt_codes))
        enhanced_features_total = sum(enhanced_features.values()) if 'enhanced_features' in locals() else 0
        
        print(f"📈 EXTRACTION PERFORMANCE:")
        print(f"   Original: {len(original_rules)} rules, {original_cpt_count} CPT codes")
        print(f"   Enhanced: {len(enhanced_rules)} rules, {enhanced_cpt_count} CPT codes, {enhanced_features_total} advanced features")
        
        if enhanced_features_total > 0:
            print(f"\n🎯 ENHANCED VALUE:")
            print(f"   ✅ Advanced pattern recognition working")
            print(f"   ✅ Context-aware authorization logic available")
            print(f"   ✅ Real-world complexity handled")
            
            improvement_areas = []
            if enhanced_features['place_of_service'] > 0:
                improvement_areas.append("Office vs Hospital settings")
            if enhanced_features['diagnosis_exceptions'] > 0:
                improvement_areas.append("Diagnosis-based exemptions")
            if enhanced_features['geographic_exceptions'] > 0:
                improvement_areas.append("State-specific rules")
            if enhanced_features['age_restrictions'] > 0:
                improvement_areas.append("Age-based authorization")
            
            print(f"   🎪 Handles: {', '.join(improvement_areas)}")
        
        print(f"\n💡 RECOMMENDATION:")
        if enhanced_features_total > 5:
            print(f"   🚀 Enhanced parser provides significant value for complex authorization scenarios")
            print(f"   🎯 Recommend migration to enhanced parser for production use")
        elif enhanced_features_total > 0:
            print(f"   📈 Enhanced parser shows promise, continue development")
            print(f"   🔄 Test with more complex documents")
        else:
            print(f"   📊 Enhanced parser needs more development for this document type")
    
    print("=" * 60)

if __name__ == "__main__":
    test_real_uhc_enhanced()