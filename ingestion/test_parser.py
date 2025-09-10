#!/usr/bin/env python3
"""Test script for UnitedHealthcare PDF parser.

This script demonstrates the full parsing pipeline:
1. Convert PDF to Markdown using marker-pdf
2. Extract tables using pdfplumber as fallback
3. Parse Markdown into structured Rule objects
4. Display and validate results
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json
from typing import List

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Activate marker virtual environment
sys.path.insert(0, '/Users/myrakirmani/Desktop/PA/marker_env/lib/python3.11/site-packages')

from ingestion.uhc_parser import (
    convert_pdf_to_markdown,
    extract_tables_with_pdfplumber,
    parse_markdown_to_rules,
    get_llm_prompt
)
from models.entities import Rule, AuthRequirement


def test_pdf_parser(pdf_path: str):
    """Test the complete PDF parsing pipeline.
    
    Args:
        pdf_path: Path to the UnitedHealthcare PDF file
    """
    print("=" * 80)
    print("UnitedHealthcare Prior Authorization PDF Parser Test")
    print("=" * 80)
    print(f"PDF File: {pdf_path}")
    print(f"Start Time: {datetime.now().isoformat()}\n")
    
    # Validate PDF exists
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF file not found at {pdf_path}")
        print("Please ensure the UnitedHealthcare PDF is placed at the specified path.")
        return
    
    # Step 1: Convert PDF to Markdown
    print("\n" + "-" * 40)
    print("Step 1: Converting PDF to Markdown")
    print("-" * 40)
    
    try:
        markdown_text = convert_pdf_to_markdown(pdf_path)
        print(f"✓ Markdown conversion successful")
        print(f"  - Text length: {len(markdown_text)} characters")
        print(f"  - Line count: {len(markdown_text.splitlines())}")
        
        # Show first 500 characters as preview
        print(f"\n  Preview of extracted text:")
        print("  " + "─" * 36)
        preview = markdown_text[:500].replace('\n', '\n  ')
        print(f"  {preview}...")
        
    except Exception as e:
        print(f"✗ Error converting PDF to Markdown: {e}")
        return
    
    # Step 2: Extract tables with pdfplumber (fallback)
    print("\n" + "-" * 40)
    print("Step 2: Extracting Tables with pdfplumber")
    print("-" * 40)
    
    try:
        tables = extract_tables_with_pdfplumber(pdf_path)
        print(f"✓ Table extraction completed")
        print(f"  - Tables found: {len(tables)}")
        
        if tables:
            # Show summary of first table
            first_table = tables[0]
            print(f"\n  First table (Page {first_table['page']}):")
            print(f"    - Headers: {first_table['headers']}")
            print(f"    - Row count: {len(first_table['rows'])}")
            
    except Exception as e:
        print(f"✗ Error extracting tables: {e}")
        # Continue even if table extraction fails
        tables = []
    
    # Step 3: Parse Markdown to Rules
    print("\n" + "-" * 40)
    print("Step 3: Parsing Markdown to Rule Objects")
    print("-" * 40)
    
    try:
        rules = parse_markdown_to_rules(markdown_text, pdf_path)
        print(f"✓ Rule parsing completed")
        print(f"  - Total rules extracted: {len(rules)}")
        
        # Analyze rules by type
        analyze_rules(rules)
        
        # Display sample rules
        display_sample_rules(rules)
        
        # Check for rules requiring LLM processing
        llm_required = [r for r in rules if r.requires_llm_processing]
        if llm_required:
            print(f"\n  ⚠ {len(llm_required)} rules require LLM processing for complex narratives")
            
            # Show example LLM prompt
            if llm_required:
                sample_rule = llm_required[0]
                print(f"\n  Example LLM prompt for complex rule:")
                print("  " + "─" * 36)
                prompt = get_llm_prompt(
                    'extract_clinical_criteria',
                    narrative_text=sample_rule.narrative_text or ""
                )
                print("  " + prompt[:300].replace('\n', '\n  ') + "...")
        
    except Exception as e:
        print(f"✗ Error parsing rules: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 4: Validate and Summary
    print("\n" + "-" * 40)
    print("Step 4: Validation and Summary")
    print("-" * 40)
    
    validation_results = validate_rules(rules)
    print(f"\nValidation Results:")
    for check, result in validation_results.items():
        status = "✓" if result['valid'] else "✗"
        print(f"  {status} {check}: {result['message']}")
    
    print("\n" + "=" * 80)
    print(f"Test completed at: {datetime.now().isoformat()}")
    print("=" * 80)


def analyze_rules(rules: List[Rule]):
    """Analyze and categorize extracted rules.
    
    Args:
        rules: List of Rule objects
    """
    if not rules:
        print("  No rules to analyze")
        return
    
    # Count by authorization requirement
    auth_counts = {}
    for rule in rules:
        auth_type = rule.auth_requirement.value
        auth_counts[auth_type] = auth_counts.get(auth_type, 0) + 1
    
    print(f"\n  Authorization Requirements:")
    for auth_type, count in auth_counts.items():
        print(f"    - {auth_type}: {count} rules")
    
    # Count by category
    categories = {}
    for rule in rules:
        cat = rule.category or "Uncategorized"
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n  Top Categories:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"    - {cat}: {count} rules")
    
    # CPT code statistics
    all_cpt_codes = set()
    for rule in rules:
        all_cpt_codes.update(rule.cpt_codes)
    
    print(f"\n  CPT/HCPCS Code Statistics:")
    print(f"    - Unique codes: {len(all_cpt_codes)}")
    print(f"    - Rules with codes: {sum(1 for r in rules if r.cpt_codes)}")
    print(f"    - Rules without codes: {sum(1 for r in rules if not r.cpt_codes)}")
    
    # State-specific rules
    state_specific = [r for r in rules if r.excluded_states or r.included_states]
    print(f"\n  State-Specific Rules: {len(state_specific)}")


def display_sample_rules(rules: List[Rule], count: int = 3):
    """Display sample rules for verification.
    
    Args:
        rules: List of Rule objects
        count: Number of samples to display
    """
    if not rules:
        return
    
    print(f"\n  Sample Rules (first {count}):")
    print("  " + "─" * 76)
    
    for i, rule in enumerate(rules[:count], 1):
        print(f"\n  Rule #{i}:")
        print(f"    Type: {rule.rule_type.value}")
        print(f"    Auth: {rule.auth_requirement.value}")
        print(f"    Category: {rule.category or 'N/A'}")
        print(f"    Service: {rule.service or 'N/A'}")
        
        if rule.cpt_codes:
            codes_preview = ', '.join(rule.cpt_codes[:5])
            if len(rule.cpt_codes) > 5:
                codes_preview += f" ... ({len(rule.cpt_codes)} total)"
            print(f"    CPT Codes: {codes_preview}")
        
        if rule.icd_codes:
            print(f"    ICD Codes: {', '.join(rule.icd_codes[:3])}")
        
        if rule.excluded_states:
            print(f"    Excluded States: {', '.join(rule.excluded_states)}")
        
        print(f"    Source: Page {rule.source_page}, Line {rule.source_line}")
        print(f"    Confidence: {rule.confidence_score:.1%}" if rule.confidence_score else "    Confidence: N/A")
        
        if rule.requires_llm_processing:
            print(f"    ⚠ Requires LLM processing")


def validate_rules(rules: List[Rule]) -> dict:
    """Validate extracted rules for quality and completeness.
    
    Args:
        rules: List of Rule objects
        
    Returns:
        Dictionary of validation results
    """
    results = {}
    
    # Check if we have rules
    results['has_rules'] = {
        'valid': len(rules) > 0,
        'message': f"Found {len(rules)} rules"
    }
    
    # Check CPT code format
    invalid_cpt = []
    for rule in rules:
        for code in rule.cpt_codes:
            # Skip range placeholders
            if code.startswith('RANGE_'):
                continue
            # Basic validation (actual validation is in the model)
            if not (len(code) == 5 or (len(code) == 5 and code[0].isalpha())):
                invalid_cpt.append(code)
    
    results['cpt_validation'] = {
        'valid': len(invalid_cpt) == 0,
        'message': f"All CPT codes valid" if not invalid_cpt else f"Found {len(invalid_cpt)} invalid codes"
    }
    
    # Check provenance information
    rules_with_provenance = [r for r in rules if r.source_page and r.source_file]
    results['provenance'] = {
        'valid': len(rules_with_provenance) == len(rules),
        'message': f"{len(rules_with_provenance)}/{len(rules)} rules have complete provenance"
    }
    
    # Check for categories
    rules_with_category = [r for r in rules if r.category]
    results['categorization'] = {
        'valid': len(rules_with_category) > len(rules) * 0.7,  # At least 70% should have categories
        'message': f"{len(rules_with_category)}/{len(rules)} rules have categories"
    }
    
    # Check confidence scores
    high_confidence = [r for r in rules if r.confidence_score and r.confidence_score >= 0.7]
    results['confidence'] = {
        'valid': len(high_confidence) > len(rules) * 0.5,  # At least 50% high confidence
        'message': f"{len(high_confidence)} rules have high confidence (≥70%)"
    }
    
    return results


def main():
    """Main entry point for testing."""
    
    # Default PDF path - update this to your actual PDF location
    DEFAULT_PDF = "data/uhc_commercial_prior_auth_2025.pdf"
    
    # Check command line arguments
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = DEFAULT_PDF
        print(f"No PDF path provided, using default: {pdf_path}")
        print("Usage: python test_parser.py [path_to_pdf]\n")
    
    # Ensure virtual environment is activated
    import marker
    print(f"Using marker from: {marker.__file__}\n")
    
    # Run the test
    try:
        test_pdf_parser(pdf_path)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()