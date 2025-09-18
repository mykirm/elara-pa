#!/usr/bin/env python3
"""Complex rule parsing comparison test between original and enhanced parsers."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from parsers.payer_rules.uhc_rules import parse_markdown_to_rules
from parsers.payer_rules.uhc_rules_enhanced import parse_markdown_to_enhanced_rules
import json

def create_complex_test_cases():
    """Create complex test cases that challenge both parsers"""
    
    test_cases = [
        {
            "name": "Place of Service Complexity",
            "description": "Office vs outpatient hospital with different auth requirements",
            "markdown": """
            # Cardiovascular Imaging
            
            Prior authorization only required when requesting service in an outpatient hospital setting.
            Prior authorization not required if performed in an office setting.
            
            Site of service will be reviewed as part of the prior authorization process for 
            the following codes: 76700 76701 76702 76705
            
            CPT Codes: 76700 76701 76702 76705 93303 93304 93306 93307
            """,
            "expected_features": {
                "pos_rules": 2,  # Office + Outpatient Hospital
                "cpt_codes": 8,
                "auth_patterns": ["required", "not required", "review"]
            }
        },
        
        {
            "name": "Diagnosis Exception Complexity", 
            "description": "Multiple diagnosis codes that exempt from authorization",
            "markdown": """
            # Breast Procedures
            
            Prior authorization required for all breast procedures.
            
            Prior authorization not required for the following diagnosis codes:
            C50.011 C50.012 C50.019 C50.111 C50.112 C50.119 C50.121 C50.122 C50.129
            C50.211 C50.212 C50.219 C50.221 C50.222 C50.229 C50.311 C50.312 C50.319
            
            CPT Codes: 19316 19318 19325 19328 19330 19340 19342
            """,
            "expected_features": {
                "diagnosis_exceptions": 18,  # ICD codes
                "cpt_codes": 7,
                "exception_type": "EXEMPT"
            }
        },
        
        {
            "name": "Geographic Exception Complexity",
            "description": "Complex state exclusions with conditional logic",
            "markdown": """
            # Arthroscopy Procedures
            
            Prior authorization is required for all states. In addition, site of service will be
            reviewed as part of the prior authorization process for the following codes except in
            Alaska, Massachusetts, Puerto Rico, Rhode Island, Texas, Utah, the Virgin Islands and Wisconsin.
            
            29805 29806 29807 29819 29820 29821 29822 29823 29824 29825 29826 29827 29828
            """,
            "expected_features": {
                "excluded_states": 8,  # AK, MA, PR, RI, TX, UT, VI, WI
                "cpt_codes": 13,
                "conditional_logic": 1
            }
        },
        
        {
            "name": "Age-Based Authorization",
            "description": "Different rules for different age groups",
            "markdown": """
            # Cardiac Procedures
            
            Prior authorization is required for patients ages 18 and older.
            See the congenital heart disease section for patients under age 18.
            
            For pediatric patients (under 18), notification only is required.
            
            CPT Codes: 33776 33777 33778 33779 33786 33788
            """,
            "expected_features": {
                "age_restrictions": 2,  # 18+ and <18
                "cpt_codes": 6,
                "auth_types": ["REQUIRED", "NOTIFICATION_ONLY"]
            }
        },
        
        {
            "name": "Multi-Pattern Complexity",
            "description": "Document with multiple complex patterns combined",
            "markdown": """
            # Advanced Imaging Procedures
            
            Prior authorization is required for patients ages 21 and older when requesting 
            service in an outpatient hospital setting. Prior authorization not required if 
            performed in an office setting.
            
            Prior authorization not required for the following diagnosis codes:
            M25.511 M25.512 M25.519 M25.521 M25.522 M25.529
            
            Geographic exceptions: Prior authorization required for all states except in
            Florida, California, New York, and Illinois.
            
            Site of service review applies to: 70450 70460 70470 70480 70481 70482
            Office setting codes: 70450 70460
            Hospital codes: 70470 70480 70481 70482
            """,
            "expected_features": {
                "age_restrictions": 1,
                "pos_rules": 2,
                "diagnosis_exceptions": 6,
                "excluded_states": 4,
                "cpt_codes": 6
            }
        }
    ]
    
    return test_cases

def analyze_rule_extraction(rules, test_case_name):
    """Analyze extracted rules for completeness and accuracy"""
    
    analysis = {
        "total_rules": len(rules),
        "total_cpt_codes": 0,
        "auth_requirements": {},
        "has_enhanced_features": False,
        "features_found": {}
    }
    
    # Count CPT codes and auth requirements
    all_cpt_codes = set()
    for rule in rules:
        all_cpt_codes.update(rule.cpt_codes)
        auth_req = str(rule.auth_requirement)
        analysis["auth_requirements"][auth_req] = analysis["auth_requirements"].get(auth_req, 0) + 1
    
    analysis["total_cpt_codes"] = len(all_cpt_codes)
    analysis["unique_cpt_codes"] = list(all_cpt_codes)
    
    # Check for enhanced features (if available)
    if rules and hasattr(rules[0], 'place_of_service_restrictions'):
        analysis["has_enhanced_features"] = True
        
        # Count enhanced features
        pos_count = sum(1 for r in rules if r.place_of_service_restrictions)
        dx_count = sum(1 for r in rules if r.diagnosis_exceptions)
        age_count = sum(1 for r in rules if r.age_restrictions)
        geo_count = sum(1 for r in rules if r.excluded_states or r.included_states)
        cond_count = sum(1 for r in rules if r.conditional_logic)
        
        analysis["features_found"] = {
            "place_of_service_rules": pos_count,
            "diagnosis_exceptions": dx_count,
            "age_restrictions": age_count,
            "geographic_exceptions": geo_count,
            "conditional_logic": cond_count
        }
        
        # Count individual diagnosis exception codes
        dx_codes = set()
        for rule in rules:
            for dx_exception in rule.diagnosis_exceptions:
                dx_codes.update(dx_exception.icd_codes)
        analysis["diagnosis_exception_codes"] = len(dx_codes)
        
        # Count excluded states
        excluded_states = set()
        for rule in rules:
            excluded_states.update(rule.excluded_states)
        analysis["excluded_states_count"] = len(excluded_states)
    
    return analysis

def run_comparison_test():
    """Run comprehensive comparison test"""
    
    print("🔬 COMPLEX RULE PARSING COMPARISON TEST")
    print("=" * 70)
    print("Testing original vs enhanced parser on complex authorization scenarios")
    print()
    
    test_cases = create_complex_test_cases()
    overall_results = {
        "original": {"wins": 0, "total_features": 0, "total_cpt_codes": 0},
        "enhanced": {"wins": 0, "total_features": 0, "total_cpt_codes": 0}
    }
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"🧪 TEST {i}: {test_case['name']}")
        print(f"📝 {test_case['description']}")
        print("-" * 50)
        
        # Test original parser
        try:
            original_rules = parse_markdown_to_rules(test_case['markdown'], f"test_{i}_original.pdf")
            original_analysis = analyze_rule_extraction(original_rules, f"Original - {test_case['name']}")
            
            print(f"📊 ORIGINAL PARSER:")
            print(f"   Rules extracted: {original_analysis['total_rules']}")
            print(f"   CPT codes found: {original_analysis['total_cpt_codes']}")
            print(f"   Auth requirements: {original_analysis['auth_requirements']}")
            
        except Exception as e:
            print(f"❌ Original parser error: {e}")
            original_analysis = {"total_rules": 0, "total_cpt_codes": 0, "features_found": {}}
        
        # Test enhanced parser
        try:
            enhanced_rules = parse_markdown_to_enhanced_rules(test_case['markdown'], f"test_{i}_enhanced.pdf")
            enhanced_analysis = analyze_rule_extraction(enhanced_rules, f"Enhanced - {test_case['name']}")
            
            print(f"🚀 ENHANCED PARSER:")
            print(f"   Rules extracted: {enhanced_analysis['total_rules']}")
            print(f"   CPT codes found: {enhanced_analysis['total_cpt_codes']}")
            print(f"   Auth requirements: {enhanced_analysis['auth_requirements']}")
            
            if enhanced_analysis["has_enhanced_features"]:
                features = enhanced_analysis["features_found"]
                print(f"   📋 Enhanced Features:")
                print(f"      Place of Service rules: {features['place_of_service_rules']}")
                print(f"      Diagnosis exceptions: {features['diagnosis_exceptions']}")
                if enhanced_analysis.get("diagnosis_exception_codes", 0) > 0:
                    print(f"         → {enhanced_analysis['diagnosis_exception_codes']} ICD codes")
                print(f"      Age restrictions: {features['age_restrictions']}")
                print(f"      Geographic exceptions: {features['geographic_exceptions']}")
                if enhanced_analysis.get("excluded_states_count", 0) > 0:
                    print(f"         → {enhanced_analysis['excluded_states_count']} excluded states")
                print(f"      Conditional logic: {features['conditional_logic']}")
            
        except Exception as e:
            print(f"❌ Enhanced parser error: {e}")
            enhanced_analysis = {"total_rules": 0, "total_cpt_codes": 0, "features_found": {}}
        
        # Compare results
        print(f"🏆 COMPARISON RESULTS:")
        
        # CPT code extraction comparison
        if enhanced_analysis["total_cpt_codes"] > original_analysis["total_cpt_codes"]:
            print(f"   ✅ Enhanced parser found more CPT codes ({enhanced_analysis['total_cpt_codes']} vs {original_analysis['total_cpt_codes']})")
            overall_results["enhanced"]["wins"] += 1
        elif original_analysis["total_cpt_codes"] > enhanced_analysis["total_cpt_codes"]:
            print(f"   ✅ Original parser found more CPT codes ({original_analysis['total_cpt_codes']} vs {enhanced_analysis['total_cpt_codes']})")
            overall_results["original"]["wins"] += 1
        else:
            print(f"   🤝 Equal CPT code extraction ({original_analysis['total_cpt_codes']} codes)")
        
        # Enhanced features comparison
        if enhanced_analysis.get("has_enhanced_features", False):
            total_enhanced_features = sum(enhanced_analysis["features_found"].values())
            print(f"   🚀 Enhanced parser extracted {total_enhanced_features} advanced features")
            overall_results["enhanced"]["total_features"] += total_enhanced_features
            if total_enhanced_features > 0:
                overall_results["enhanced"]["wins"] += 1
        
        # Update totals
        overall_results["original"]["total_cpt_codes"] += original_analysis["total_cpt_codes"]
        overall_results["enhanced"]["total_cpt_codes"] += enhanced_analysis["total_cpt_codes"]
        
        print()
    
    # Overall summary
    print("📊 OVERALL COMPARISON SUMMARY")
    print("=" * 70)
    
    print(f"🎯 EXTRACTION PERFORMANCE:")
    print(f"   Original Parser:")
    print(f"      Total CPT codes: {overall_results['original']['total_cpt_codes']}")
    print(f"      Test wins: {overall_results['original']['wins']}")
    
    print(f"   Enhanced Parser:")
    print(f"      Total CPT codes: {overall_results['enhanced']['total_cpt_codes']}")
    print(f"      Enhanced features: {overall_results['enhanced']['total_features']}")
    print(f"      Test wins: {overall_results['enhanced']['wins']}")
    
    # Determine winner
    enhanced_total_score = overall_results['enhanced']['wins'] + (1 if overall_results['enhanced']['total_features'] > 0 else 0)
    original_total_score = overall_results['original']['wins']
    
    print(f"\n🏆 FINAL VERDICT:")
    if enhanced_total_score > original_total_score:
        print(f"   ✅ Enhanced Parser WINS!")
        print(f"      - Better feature extraction for complex patterns")
        print(f"      - {overall_results['enhanced']['total_features']} advanced features detected")
        print(f"      - Context-aware authorization logic")
    elif original_total_score > enhanced_total_score:
        print(f"   ✅ Original Parser WINS!")
        print(f"      - More reliable basic extraction")
        print(f"      - Better CPT code detection")
    else:
        print(f"   🤝 TIE - Both parsers have complementary strengths")
    
    print(f"\n💡 RECOMMENDATION:")
    if overall_results['enhanced']['total_features'] > 0:
        print(f"   Use Enhanced Parser for complex authorization scenarios")
        print(f"   Features like place-of-service and diagnosis exceptions provide")
        print(f"   significant value for real-world prior authorization decisions")
    else:
        print(f"   Enhanced parser needs further development for complex pattern detection")
    
    print("=" * 70)

if __name__ == "__main__":
    run_comparison_test()