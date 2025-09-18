#!/usr/bin/env python3
"""
Quick Prior Authorization Test
=============================

Simple script to test PA decisions with sample cases.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from interactive_pa_system import InteractivePASystem


def test_common_scenarios():
    """Test common prior authorization scenarios"""
    
    system = InteractivePASystem()
    
    print("🧪 TESTING COMMON PA SCENARIOS")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        {
            'name': 'Knee Replacement (Arthroplasty)',
            'patient': {'age': 65, 'state': 'CA', 'payer': 'UnitedHealthcare'},
            'procedure': {'cpt_codes': ['27447'], 'icd_codes': ['M17.9']}
        },
        {
            'name': 'Arthroscopy',
            'patient': {'age': 30, 'state': 'TX', 'payer': 'UnitedHealthcare'},
            'procedure': {'cpt_codes': ['29881'], 'icd_codes': ['M23.9']}
        },
        {
            'name': 'Bariatric Surgery',
            'patient': {'age': 40, 'state': 'NY', 'payer': 'UnitedHealthcare'},
            'procedure': {'cpt_codes': ['43644'], 'icd_codes': ['E66.01']}
        },
        {
            'name': 'Breast Reconstruction',
            'patient': {'age': 45, 'state': 'FL', 'payer': 'UnitedHealthcare'},
            'procedure': {'cpt_codes': ['19316'], 'icd_codes': ['C50.911']}
        },
        {
            'name': 'Regular Office Visit',
            'patient': {'age': 35, 'state': 'CA', 'payer': 'UnitedHealthcare'},
            'procedure': {'cpt_codes': ['99213'], 'icd_codes': ['Z00.00']}
        }
    ]
    
    results = []
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {case['name']}")
        print("-" * 40)
        
        # Set defaults
        patient_info = {
            'patient_id': f'TEST_{i:03d}',
            'plan_type': 'PPO',
            **case['patient']
        }
        
        procedure_info = {
            'place_of_service': '22',
            'place_of_service_desc': 'Outpatient Hospital',
            'provider_specialty': 'Internal Medicine',
            **case['procedure']
        }
        
        # Evaluate
        evaluation = system.evaluate_authorization(patient_info, procedure_info)
        
        # Display summary
        auth_status = "🔴 REQUIRED" if evaluation['authorization_required'] else "🟢 NOT REQUIRED"
        print(f"Result: {auth_status}")
        print(f"Type: {evaluation['authorization_type']}")
        print(f"Matching Rules: {len(evaluation['matching_rules'])}")
        
        if evaluation['matching_rules']:
            for match in evaluation['matching_rules']:
                rule = match['rule']
                matched_cpts = match['match_details']['matched_cpt_codes']
                print(f"  • Matched CPT: {matched_cpts} → {rule.auth_requirement.value}")
        
        results.append({
            'case': case['name'],
            'authorization_required': evaluation['authorization_required'],
            'authorization_type': evaluation['authorization_type'],
            'matching_rules_count': len(evaluation['matching_rules'])
        })
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    for result in results:
        status = "🔴 REQ" if result['authorization_required'] else "🟢 OK"
        print(f"{status} | {result['case']:<25} | {result['authorization_type']:<15} | {result['matching_rules_count']} rules")
    
    return results


if __name__ == "__main__":
    test_common_scenarios()
