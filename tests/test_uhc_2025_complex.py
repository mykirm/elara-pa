#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test of UHC 2025 PA Requirements PDF
Testing complex authorization scenarios with manual verification
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from parsers.pdf_extractor import convert_pdf_to_markdown
from parsers.payer_rules.uhc_rules import parse_markdown_to_rules
from parsers.enhanced_rule_parser import EnhancedRuleParser
from preprocessing.intelligent_chunker import BasicIntelligentChunker

def test_uhc_2025_complex():
    """Test complex scenarios in UHC 2025 PA Requirements"""
    
    print("=" * 80)
    print("UHC 2025 PA REQUIREMENTS - COMPREHENSIVE TEST")
    print("=" * 80)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Convert PDF to Markdown
    pdf_path = "data/UHC-Commercial-PA-Requirements-2025.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF not found at {pdf_path}")
        return
    
    print("STEP 1: PDF TO MARKDOWN CONVERSION")
    print("-" * 40)
    
    try:
        markdown_text = convert_pdf_to_markdown(pdf_path, output_prefix="uhc_2025")
        print(f"✓ Converted PDF to Markdown: {len(markdown_text):,} characters")
        
        # Save markdown for manual review
        markdown_path = f"data/processed/uhc_2025_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_text)
        print(f"✓ Saved markdown to: {markdown_path}")
        
    except Exception as e:
        print(f"✗ Conversion failed: {e}")
        return
    
    # Step 2: Test Original Parser
    print("\nSTEP 2: ORIGINAL PARSER ANALYSIS")
    print("-" * 40)
    
    try:
        original_rules = parse_markdown_to_rules(markdown_text, pdf_path)
        print(f"✓ Original parser extracted: {len(original_rules)} rules")
        
        # Analyze original results
        original_stats = analyze_rules(original_rules, "ORIGINAL")
        
    except Exception as e:
        print(f"✗ Original parser failed: {e}")
        original_rules = []
        original_stats = {}
    
    # Step 3: Test Enhanced Parser with Chunking
    print("\nSTEP 3: ENHANCED PARSER WITH INTELLIGENT CHUNKING")
    print("-" * 40)
    
    try:
        enhanced_parser = EnhancedRuleParser()
        enhanced_rules, chunks = enhanced_parser.parse_with_preprocessing(markdown_text, pdf_path)
        print(f"✓ Enhanced parser extracted: {len(enhanced_rules)} rules from {len(chunks)} chunks")
        
        # Analyze chunks
        print(f"\nChunk Analysis:")
        chunk_types = {}
        for chunk in chunks:
            chunk_types[chunk.content_type] = chunk_types.get(chunk.content_type, 0) + 1
        
        for ctype, count in sorted(chunk_types.items()):
            print(f"  {ctype}: {count} chunks")
        
        # Analyze enhanced results
        enhanced_stats = analyze_rules(enhanced_rules, "ENHANCED")
        
    except Exception as e:
        print(f"✗ Enhanced parser failed: {e}")
        enhanced_rules = []
        enhanced_stats = {}
        chunks = []
    
    # Step 4: Complex Scenario Testing
    print("\nSTEP 4: COMPLEX SCENARIO TESTING")
    print("-" * 40)
    
    test_complex_scenarios(original_rules, enhanced_rules, chunks)
    
    # Step 5: Manual Verification Guide
    print("\nSTEP 5: MANUAL VERIFICATION GUIDE")
    print("-" * 40)
    
    create_verification_guide(original_rules, enhanced_rules, chunks, markdown_path)
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

def analyze_rules(rules, parser_name):
    """Analyze extracted rules for key metrics"""
    
    stats = {
        'total_rules': len(rules),
        'cpt_codes': set(),
        'auth_required': 0,
        'auth_not_required': 0,
        'auth_conditional': 0,
        'auth_notification': 0,
        'states_with_exceptions': set(),
        'categories': set(),
        'services': set(),
        'rules_with_icd': 0,
        'rules_with_age_limits': 0,
        'rules_with_quantity_limits': 0,
        'high_confidence': 0,
        'requires_llm': 0
    }
    
    for rule in rules:
        # CPT codes
        if rule.cpt_codes:
            stats['cpt_codes'].update(rule.cpt_codes)
        
        # Authorization types
        if rule.auth_requirement.value == 'REQUIRED':
            stats['auth_required'] += 1
        elif rule.auth_requirement.value == 'NOT_REQUIRED':
            stats['auth_not_required'] += 1
        elif rule.auth_requirement.value == 'CONDITIONAL':
            stats['auth_conditional'] += 1
        elif rule.auth_requirement.value == 'NOTIFICATION_ONLY':
            stats['auth_notification'] += 1
        
        # Geographic exceptions
        if hasattr(rule, 'excluded_states') and rule.excluded_states:
            stats['states_with_exceptions'].update(rule.excluded_states)
        
        # Categories and services
        if rule.category:
            stats['categories'].add(rule.category)
        if rule.service:
            stats['services'].add(rule.service)
        
        # Complex conditions
        if rule.icd_codes:
            stats['rules_with_icd'] += 1
        if rule.age_min or rule.age_max:
            stats['rules_with_age_limits'] += 1
        if rule.quantity_limit:
            stats['rules_with_quantity_limits'] += 1
        
        # Quality metrics
        if hasattr(rule, 'confidence_score') and rule.confidence_score and rule.confidence_score > 0.8:
            stats['high_confidence'] += 1
        if rule.requires_llm_processing:
            stats['requires_llm'] += 1
    
    # Print analysis
    print(f"\n{parser_name} Parser Results:")
    print(f"  Total rules: {stats['total_rules']}")
    print(f"  Unique CPT codes: {len(stats['cpt_codes'])}")
    print(f"  Authorization breakdown:")
    print(f"    - Required: {stats['auth_required']}")
    print(f"    - Not Required: {stats['auth_not_required']}")
    print(f"    - Conditional: {stats['auth_conditional']}")
    print(f"    - Notification Only: {stats['auth_notification']}")
    print(f"  Categories: {len(stats['categories'])}")
    print(f"  Services: {len(stats['services'])}")
    print(f"  States with exceptions: {len(stats['states_with_exceptions'])} ({', '.join(sorted(stats['states_with_exceptions'])[:5])}...)")
    print(f"  Complex rules:")
    print(f"    - With ICD codes: {stats['rules_with_icd']}")
    print(f"    - With age limits: {stats['rules_with_age_limits']}")
    print(f"    - With quantity limits: {stats['rules_with_quantity_limits']}")
    
    if parser_name == "ENHANCED":
        print(f"  Quality metrics:")
        print(f"    - High confidence (>0.8): {stats['high_confidence']}")
        print(f"    - Requires LLM processing: {stats['requires_llm']}")
    
    return stats

def test_complex_scenarios(original_rules, enhanced_rules, chunks):
    """Test specific complex authorization scenarios"""
    
    scenarios = [
        {
            'name': 'Multi-CPT Authorization',
            'description': 'Rules with multiple CPT codes in a single rule',
            'test': lambda r: len(r.cpt_codes) > 3
        },
        {
            'name': 'Geographic Exceptions',
            'description': 'Rules with state-specific exceptions',
            'test': lambda r: hasattr(r, 'excluded_states') and len(r.excluded_states) > 0
        },
        {
            'name': 'ICD-Based Authorization',
            'description': 'Rules requiring specific diagnoses',
            'test': lambda r: len(r.icd_codes) > 0
        },
        {
            'name': 'Age-Restricted Services',
            'description': 'Rules with age limitations',
            'test': lambda r: r.age_min is not None or r.age_max is not None
        },
        {
            'name': 'Quantity Limited Services',
            'description': 'Rules with quantity/frequency limits',
            'test': lambda r: r.quantity_limit is not None
        },
        {
            'name': 'CPT Ranges',
            'description': 'Rules with CPT code ranges (e.g., 29805-29825)',
            'test': lambda r: any('RANGE_' in code or '-' in code for code in r.cpt_codes)
        },
        {
            'name': 'HCPCS Codes',
            'description': 'Rules with HCPCS codes (letter + 4 digits)',
            'test': lambda r: any(code[0].isalpha() and len(code) == 5 for code in r.cpt_codes)
        }
    ]
    
    print("\nComplex Scenario Results:")
    print("-" * 40)
    
    for scenario in scenarios:
        orig_count = len([r for r in original_rules if scenario['test'](r)])
        enh_count = len([r for r in enhanced_rules if scenario['test'](r)])
        
        status = "✓" if enh_count >= orig_count else "✗"
        diff = f"+{enh_count - orig_count}" if enh_count > orig_count else f"{enh_count - orig_count}"
        
        print(f"{status} {scenario['name']}:")
        print(f"   {scenario['description']}")
        print(f"   Original: {orig_count} | Enhanced: {enh_count} ({diff})")
        
        # Show examples from enhanced parser
        if enh_count > 0:
            examples = [r for r in enhanced_rules if scenario['test'](r)][:2]
            for i, rule in enumerate(examples, 1):
                if scenario['name'] == 'Multi-CPT Authorization':
                    print(f"   Example {i}: {len(rule.cpt_codes)} CPT codes - {', '.join(rule.cpt_codes[:5])}...")
                elif scenario['name'] == 'Geographic Exceptions':
                    print(f"   Example {i}: Excluded states - {', '.join(rule.excluded_states[:5])}")
                elif scenario['name'] == 'ICD-Based Authorization':
                    print(f"   Example {i}: ICD codes - {', '.join(rule.icd_codes[:3])}")
        print()

def create_verification_guide(original_rules, enhanced_rules, chunks, markdown_path):
    """Create manual verification guide"""
    
    print("\n" + "=" * 80)
    print("MANUAL VERIFICATION GUIDE")
    print("=" * 80)
    
    print("\n📋 HOW TO MANUALLY VERIFY RESULTS:")
    print("-" * 40)
    
    print("\n1. REVIEW MARKDOWN OUTPUT:")
    print(f"   Open: {markdown_path}")
    print("   Search for these key phrases:")
    print("   - 'prior authorization required'")
    print("   - 'notification required'")
    print("   - 'does not require'")
    print("   - 'except' (for geographic exceptions)")
    print("   - CPT code patterns: 5-digit numbers (e.g., 29826)")
    print("   - HCPCS patterns: Letter + 4 digits (e.g., A0425)")
    
    print("\n2. CHECK RULE EXTRACTION:")
    
    # Sample some rules for verification
    if enhanced_rules:
        print("\n   Sample Rules to Verify (Enhanced Parser):")
        for i, rule in enumerate(enhanced_rules[:3], 1):
            print(f"\n   Rule {i}:")
            print(f"   - Auth: {rule.auth_requirement.value}")
            print(f"   - CPT Codes: {', '.join(rule.cpt_codes[:5])}...")
            print(f"   - Category: {rule.category}")
            print(f"   - Service: {rule.service}")
            if rule.excluded_states:
                print(f"   - Excluded States: {', '.join(rule.excluded_states)}")
            if hasattr(rule, 'confidence_score') and rule.confidence_score:
                print(f"   - Confidence: {rule.confidence_score:.2f}")
    
    print("\n3. VERIFY CHUNKING QUALITY:")
    
    if chunks:
        # Show chunk distribution
        chunk_quality = {
            'high_conf': len([c for c in chunks if c.confidence_score > 0.8]),
            'med_conf': len([c for c in chunks if 0.5 <= c.confidence_score <= 0.8]),
            'low_conf': len([c for c in chunks if c.confidence_score < 0.5])
        }
        
        print(f"   Chunk Confidence Distribution:")
        print(f"   - High (>0.8): {chunk_quality['high_conf']} chunks")
        print(f"   - Medium (0.5-0.8): {chunk_quality['med_conf']} chunks")
        print(f"   - Low (<0.5): {chunk_quality['low_conf']} chunks")
        
        # Sample chunks for review
        print("\n   Sample Chunks to Review:")
        for chunk_type in ['authorization_rule', 'geographic_exception', 'procedure_list']:
            type_chunks = [c for c in chunks if c.content_type == chunk_type][:1]
            if type_chunks:
                chunk = type_chunks[0]
                print(f"\n   {chunk_type.upper()} Chunk:")
                print(f"   - Confidence: {chunk.confidence_score:.2f}")
                print(f"   - CPT codes found: {len(chunk.extraction_hints.get('cpt_codes', []))}")
                print(f"   - States found: {len(chunk.extraction_hints.get('states', []))}")
                print(f"   - Content preview: {chunk.primary_content[:100]}...")
    
    print("\n4. COMPARISON CHECKLIST:")
    print("   □ Total rule count (Enhanced should be >= Original)")
    print("   □ CPT code coverage (Check for missing codes)")
    print("   □ Geographic exceptions (States properly detected)")
    print("   □ Authorization types (REQUIRED/NOT_REQUIRED/etc.)")
    print("   □ Complex rules (ICD codes, age limits, quantities)")
    
    print("\n5. OUTPUT FILES TO REVIEW:")
    
    # List generated files
    output_files = [
        markdown_path,
        f"data/processed/uhc_2025_*_rules_*.json",
        f"data/processed/uhc_2025_*_summary_*.txt"
    ]
    
    for pattern in output_files:
        print(f"   - {pattern}")
    
    print("\n6. QUICK VALIDATION COMMANDS:")
    print("   # Count CPT codes in markdown:")
    print(f"   grep -oE '\\b[0-9]{{5}}\\b' {markdown_path} | sort -u | wc -l")
    print("\n   # Find authorization language:")
    print(f"   grep -i 'authorization required' {markdown_path} | head -5")
    print("\n   # Check for state exceptions:")
    print(f"   grep -E '\\b(CA|NY|TX|FL)\\b' {markdown_path} | head -5")

if __name__ == "__main__":
    test_uhc_2025_complex()