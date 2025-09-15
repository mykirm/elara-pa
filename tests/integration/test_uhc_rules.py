#!/usr/bin/env python3
"""
Test script specifically for UHC Parser Rules functionality.

This script tests the rule parsing logic without requiring a PDF file,
using sample markdown text to verify the rule extraction works correctly.
"""

import sys
import os
from pathlib import Path
from typing import List

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Import our modules
from models.entities import Rule, AuthRequirement, RuleType
from src.parsers.payer_rules.uhc_rules import (
    parse_markdown_to_rules,
    merge_related_rules,
    get_llm_prompt
)


def test_cpt_code_extraction():
    """Test extraction of CPT codes from sample text."""
    print("\n" + "="*60)
    print("Testing CPT Code Extraction")
    print("="*60)
    
    sample_text = """
    PRIOR AUTHORIZATION REQUIRED FOR THE FOLLOWING SERVICES:
    
    Surgical Procedures
    27447 - Arthroplasty, knee, condyle and plateau
    27448 - Osteotomy, femur, shaft or supracondylar
    29881 - Arthroscopy, knee, surgical
    
    Diagnostic Imaging
    70450-70470 - CT scan of head or brain
    72125 - CT scan of cervical spine
    
    Prior authorization required except in emergency situations.
    No prior authorization required for 99213, 99214 office visits.
    """
    
    rules = parse_markdown_to_rules(sample_text, "test_cpt.md")
    
    print(f"✓ Extracted {len(rules)} rules")
    
    for i, rule in enumerate(rules, 1):
        print(f"\nRule {i}:")
        print(f"  - Type: {rule.rule_type}")
        print(f"  - Auth Requirement: {rule.auth_requirement}")
        print(f"  - CPT Codes: {rule.cpt_codes}")
        print(f"  - Category: {rule.category}")
        print(f"  - Service: {rule.service}")
        print(f"  - Confidence: {rule.confidence_score}")
    
    return rules


def test_state_exceptions():
    """Test extraction of state-specific exceptions."""
    print("\n" + "="*60)
    print("Testing State Exception Extraction")
    print("="*60)
    
    sample_text = """
    Prior authorization required for all states except CA, NY, and TX.
    
    CPT Code 12345 - Special procedure
    Available only in FL, GA, and SC.
    
    Code 67890 - Another service
    Prior authorization required excluding AL and MS.
    """
    
    rules = parse_markdown_to_rules(sample_text, "test_states.md")
    
    print(f"✓ Extracted {len(rules)} rules")
    
    for i, rule in enumerate(rules, 1):
        print(f"\nRule {i}:")
        print(f"  - CPT Codes: {rule.cpt_codes}")
        print(f"  - Excluded States: {rule.excluded_states}")
        print(f"  - Included States: {rule.included_states}")
        print(f"  - Auth Requirement: {rule.auth_requirement}")
    
    return rules


def test_complex_narrative():
    """Test detection of complex narratives requiring LLM processing."""
    print("\n" + "="*60)
    print("Testing Complex Narrative Detection")
    print("="*60)
    
    sample_text = """
    CPT Code 54321 - Advanced procedure
    Prior authorization required when used for chronic pain management
    following criteria must be met:
    - Patient must have failed conservative therapy for at least 6 weeks
    - Clinical indications must include documented MRI findings
    - Medical necessity must be established through peer review
    
    Simple procedure 98765 - No prior authorization required.
    """
    
    rules = parse_markdown_to_rules(sample_text, "test_complex.md")
    
    print(f"✓ Extracted {len(rules)} rules")
    
    for i, rule in enumerate(rules, 1):
        print(f"\nRule {i}:")
        print(f"  - CPT Codes: {rule.cpt_codes}")
        print(f"  - Requires LLM: {rule.requires_llm_processing}")
        print(f"  - Narrative: {rule.narrative_text}")
        print(f"  - Confidence: {rule.confidence_score}")
        
        if rule.requires_llm_processing:
            print(f"  - LLM Prompt Sample:")
            prompt = get_llm_prompt(
                'extract_clinical_criteria',
                narrative_text=rule.narrative_text
            )
            print(f"    {prompt[:200]}...")
    
    return rules


def test_rule_merging():
    """Test merging of related rules."""
    print("\n" + "="*60)
    print("Testing Rule Merging")
    print("="*60)
    
    sample_text = """
    SURGICAL PROCEDURES
    Prior authorization required:
    27447 - Knee arthroplasty
    27448 - Femur osteotomy
    
    SURGICAL PROCEDURES  
    Additional codes requiring prior authorization:
    29881 - Knee arthroscopy
    29882 - Knee arthroscopy with meniscectomy
    """
    
    rules = parse_markdown_to_rules(sample_text, "test_merge.md")
    print(f"✓ Initial extraction: {len(rules)} rules")
    
    merged_rules = merge_related_rules(rules)
    print(f"✓ After merging: {len(merged_rules)} rules")
    
    for i, rule in enumerate(merged_rules, 1):
        print(f"\nMerged Rule {i}:")
        print(f"  - Category: {rule.category}")
        print(f"  - CPT Codes: {rule.cpt_codes}")
        print(f"  - Total Codes: {len(rule.cpt_codes)}")
    
    return merged_rules


def test_auth_requirement_detection():
    """Test detection of different authorization requirement types."""
    print("\n" + "="*60)
    print("Testing Authorization Requirement Detection")
    print("="*60)
    
    sample_text = """
    Code 11111 - Prior authorization required
    Code 22222 - No prior authorization required  
    Code 33333 - Notification only required
    Code 44444 - Requires prior authorization for all procedures
    Code 55555 - No PA required for emergency cases
    Code 66666 - Notify only within 24 hours
    """
    
    rules = parse_markdown_to_rules(sample_text, "test_auth_types.md")
    
    print(f"✓ Extracted {len(rules)} rules")
    
    auth_types = {}
    for rule in rules:
        auth_type = rule.auth_requirement.value
        if auth_type not in auth_types:
            auth_types[auth_type] = []
        auth_types[auth_type].append(rule.cpt_codes[0] if rule.cpt_codes else "Unknown")
    
    print("\nAuthorization Requirements Detected:")
    for auth_type, codes in auth_types.items():
        print(f"  - {auth_type}: {codes}")
    
    return rules


def test_confidence_scoring():
    """Test confidence scoring for different types of extractions."""
    print("\n" + "="*60)
    print("Testing Confidence Scoring")
    print("="*60)
    
    # High confidence: clear, simple patterns
    high_conf_text = "99213 - Office visit, no prior authorization required"
    
    # Medium confidence: some ambiguity
    med_conf_text = "Procedure 12345 may require authorization depending on circumstances"
    
    # Low confidence: complex narrative
    low_conf_text = """
    Special procedure 67890 when used for complex conditions
    following criteria must be established through comprehensive evaluation
    """
    
    texts = [
        ("High Confidence", high_conf_text),
        ("Medium Confidence", med_conf_text), 
        ("Low Confidence", low_conf_text)
    ]
    
    for label, text in texts:
        rules = parse_markdown_to_rules(text, f"test_{label.lower().replace(' ', '_')}.md")
        if rules:
            rule = rules[0]
            print(f"\n{label} Test:")
            print(f"  - Text: {text[:50]}...")
            print(f"  - Confidence Score: {rule.confidence_score}")
            print(f"  - Requires LLM: {rule.requires_llm_processing}")


def run_all_tests():
    """Run all UHC parser rules tests."""
    print("🧪 UHC Parser Rules Test Suite")
    print("=" * 80)
    
    try:
        # Create data directories if they don't exist
        os.makedirs("data/raw", exist_ok=True)
        os.makedirs("data/processed", exist_ok=True)
        
        # Run individual tests
        test_cpt_code_extraction()
        test_state_exceptions()
        test_complex_narrative()
        test_rule_merging()
        test_auth_requirement_detection()
        test_confidence_scoring()
        
        print("\n" + "="*80)
        print("✅ All tests completed successfully!")
        print("📁 Check data/processed/ for generated rule files")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
