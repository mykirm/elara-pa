#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compare enhanced parser vs original parser"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from parsers.payer_rules.uhc_rules import parse_markdown_to_rules
from parsers.enhanced_rule_parser import EnhancedRuleParser

def test_enhanced_vs_original():
    """Compare enhanced vs original parser on sample data"""
    print("Enhanced vs Original Parser Comparison\n")
    
    # Sample UHC content for testing
    test_content = """
# Orthopedic Procedures

## Arthroscopic Procedures  
Prior authorization is required for the following procedures:

CPT codes 29826, 29827, 29828 require prior authorization.

Additional procedures requiring PA:
- 29880 (Arthroscopy, knee, surgical)
- 29881 (Arthroscopy, knee, surgical with meniscectomy)

## Geographic Exceptions
The following states are excluded from prior authorization requirements:
- California (CA) 
- New York (NY)
- Texas (TX)

Exception: CPT codes 29805-29825 do not require prior authorization in these states.

## Diagnostic Imaging
MRI procedures (CPT codes 72148, 72149) require prior authorization when used for chronic pain diagnosis.

Notification only required for emergency procedures in all states except FL.

## Radiology Services
CT Angiography (CPT 75571, 75572, 75573) requires prior authorization.
HCPCS codes A0425, B4150 are covered without authorization.
"""
    
    print("Test Content:")
    print(f"   Length: {len(test_content)} characters")
    print(f"   Expected CPT codes: 29826, 29827, 29828, 29880, 29881, 29805-29825, 72148, 72149, 75571, 75572, 75573")
    print(f"   Expected HCPCS: A0425, B4150") 
    print(f"   Expected states: CA, NY, TX, FL")
    
    # Test 1: Original Parser
    print("\nTesting Original Parser...")
    try:
        original_rules = parse_markdown_to_rules(test_content, "test.pdf")
        print(f"Original parser: {len(original_rules)} rules extracted")
        
        # Analyze original results
        original_cpt_codes = set()
        original_auth_required = 0
        original_auth_not_required = 0
        original_excluded_states = set()
        
        for rule in original_rules:
            original_cpt_codes.update(rule.cpt_codes)
            if hasattr(rule, 'excluded_states') and rule.excluded_states:
                original_excluded_states.update(rule.excluded_states)
            
            if rule.auth_requirement.value == 'REQUIRED':
                original_auth_required += 1
            elif rule.auth_requirement.value == 'NOT_REQUIRED':
                original_auth_not_required += 1
        
        print(f"   CPT codes found: {len(original_cpt_codes)}")
        print(f"   Authorization REQUIRED: {original_auth_required}")
        print(f"   Authorization NOT_REQUIRED: {original_auth_not_required}")
        print(f"   States with exceptions: {len(original_excluded_states)}")
        
    except Exception as e:
        print(f"Original parser failed: {e}")
        original_rules = []
        original_cpt_codes = set()
        original_excluded_states = set()
    
    # Test 2: Enhanced Parser
    print("\nTesting Enhanced Parser...")
    try:
        enhanced_parser = EnhancedRuleParser()
        enhanced_rules, chunks = enhanced_parser.parse_with_preprocessing(test_content, "test.pdf")
        print(f"Enhanced parser: {len(enhanced_rules)} rules from {len(chunks)} chunks")
        
        # Analyze enhanced results
        enhanced_cpt_codes = set()
        enhanced_auth_required = 0
        enhanced_auth_not_required = 0
        enhanced_excluded_states = set()
        
        for rule in enhanced_rules:
            enhanced_cpt_codes.update(rule.cpt_codes)
            if hasattr(rule, 'excluded_states') and rule.excluded_states:
                enhanced_excluded_states.update(rule.excluded_states)
            
            if rule.auth_requirement.value == 'REQUIRED':
                enhanced_auth_required += 1
            elif rule.auth_requirement.value == 'NOT_REQUIRED':
                enhanced_auth_not_required += 1
        
        print(f"   CPT codes found: {len(enhanced_cpt_codes)}")
        print(f"   Authorization REQUIRED: {enhanced_auth_required}")
        print(f"   Authorization NOT_REQUIRED: {enhanced_auth_not_required}")
        print(f"   States with exceptions: {len(enhanced_excluded_states)}")
        
        # Analyze chunks
        chunk_types = {}
        for chunk in chunks:
            chunk_types[chunk.content_type] = chunk_types.get(chunk.content_type, 0) + 1
        print(f"   Chunk breakdown: {chunk_types}")
        
    except Exception as e:
        print(f"Enhanced parser failed: {e}")
        enhanced_rules = []
        enhanced_cpt_codes = set()
        enhanced_excluded_states = set()
        chunks = []
    
    # Test 3: Comparison Analysis
    print("\nComparison Results:")
    
    if original_rules and enhanced_rules:
        print(f"\n   Rule Count:")
        print(f"     Original: {len(original_rules)}")
        print(f"     Enhanced: {len(enhanced_rules)}")
        print(f"     Difference: {len(enhanced_rules) - len(original_rules):+d}")
        
        print(f"\n   CPT Code Detection:")
        print(f"     Original: {len(original_cpt_codes)} codes")
        print(f"     Enhanced: {len(enhanced_cpt_codes)} codes")
        
        # Find improvements
        new_codes = enhanced_cpt_codes - original_cpt_codes
        missed_codes = original_cpt_codes - enhanced_cpt_codes
        
        if new_codes:
            print(f"     Additional codes found: {sorted(list(new_codes))}")
        if missed_codes:
            print(f"     Codes missed: {sorted(list(missed_codes))}")
        
        print(f"\n   Geographic Exception Detection:")
        print(f"     Original: {sorted(list(original_excluded_states))}")
        print(f"     Enhanced: {sorted(list(enhanced_excluded_states))}")
        
        new_states = enhanced_excluded_states - original_excluded_states
        if new_states:
            print(f"     Additional states found: {sorted(list(new_states))}")
    
    # Test 4: Check specific capabilities
    print(f"\nCapability Analysis:")
    
    # Check for HCPCS detection
    hcpcs_codes = {'A0425', 'B4150'}
    original_found_hcpcs = hcpcs_codes & original_cpt_codes
    enhanced_found_hcpcs = hcpcs_codes & enhanced_cpt_codes
    
    print(f"   HCPCS Detection:")
    print(f"     Original: {len(original_found_hcpcs)}/2 codes")
    print(f"     Enhanced: {len(enhanced_found_hcpcs)}/2 codes")
    
    # Check for range detection (29805-29825)
    range_codes = {str(i) for i in range(29805, 29826)}
    original_range_found = len(range_codes & original_cpt_codes)
    enhanced_range_found = len(range_codes & enhanced_cpt_codes)
    
    print(f"   CPT Range Detection (29805-29825):")
    print(f"     Original: {original_range_found}/21 codes")
    print(f"     Enhanced: {enhanced_range_found}/21 codes")
    
    # Overall assessment
    print(f"\nOverall Assessment:")
    
    improvements = []
    issues = []
    
    if len(enhanced_cpt_codes) > len(original_cpt_codes):
        improvements.append(f"Found {len(enhanced_cpt_codes) - len(original_cpt_codes)} more CPT codes")
    elif len(enhanced_cpt_codes) < len(original_cpt_codes):
        issues.append(f"Missed {len(original_cpt_codes) - len(enhanced_cpt_codes)} CPT codes")
    
    if len(enhanced_excluded_states) > len(original_excluded_states):
        improvements.append(f"Better geographic exception detection")
    
    if enhanced_found_hcpcs > original_found_hcpcs:
        improvements.append("Better HCPCS code detection")
    
    if improvements:
        print("   Improvements:")
        for improvement in improvements:
            print(f"     - {improvement}")
    
    if issues:
        print("   Issues:")
        for issue in issues:
            print(f"     - {issue}")
    
    if not improvements and not issues:
        print("   Results are comparable")
    
    print(f"\nComparison complete!")

if __name__ == "__main__":
    test_enhanced_vs_original()