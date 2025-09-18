#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test enhanced parser with real UHC data"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from parsers.payer_rules.uhc_rules import parse_markdown_to_rules
from parsers.enhanced_rule_parser import EnhancedRuleParser

def test_with_real_uhc_data():
    """Test both parsers with actual UHC markdown data"""
    print("Testing with Real UHC Data\n")
    
    # Find the UHC markdown file
    uhc_markdown_path = "data/raw/marker_5pages_20250910_175450/UHC-Commercial-PA-Requirements-2025/UHC-Commercial-PA-Requirements-2025.md"
    
    if not os.path.exists(uhc_markdown_path):
        # Try fallback path
        uhc_markdown_path = "data/raw/UHC-Commercial-PA-Requirements-2025_20250910_164134_fallback.md"
    
    if not os.path.exists(uhc_markdown_path):
        print("UHC markdown file not found")
        return
    
    # Load the UHC content
    print(f"Loading UHC data from: {uhc_markdown_path}")
    with open(uhc_markdown_path, 'r', encoding='utf-8') as f:
        uhc_content = f.read()
    
    # Take a smaller sample for testing
    sample_content = uhc_content[:5000]  # First 5KB
    print(f"Testing with sample: {len(sample_content)} characters")
    
    # Test 1: Original Parser
    print("\nTesting Original Parser...")
    try:
        original_rules = parse_markdown_to_rules(sample_content, "UHC-test.pdf")
        print(f"Original parser: {len(original_rules)} rules extracted")
        
        # Analyze original results
        original_cpt_codes = set()
        original_auth_required = 0
        original_excluded_states = set()
        
        for rule in original_rules:
            original_cpt_codes.update(rule.cpt_codes)
            if hasattr(rule, 'excluded_states') and rule.excluded_states:
                original_excluded_states.update(rule.excluded_states)
            
            if rule.auth_requirement.value == 'REQUIRED':
                original_auth_required += 1
        
        print(f"   CPT codes found: {sorted(list(original_cpt_codes))}")
        print(f"   Total CPT codes: {len(original_cpt_codes)}")
        print(f"   Authorization REQUIRED: {original_auth_required}")
        print(f"   States with exceptions: {sorted(list(original_excluded_states))}")
        
    except Exception as e:
        print(f"Original parser failed: {e}")
        original_rules = []
        original_cpt_codes = set()
    
    # Test 2: Enhanced Parser with Debugging
    print("\nTesting Enhanced Parser...")
    try:
        enhanced_parser = EnhancedRuleParser()
        
        # First, let's see what chunks are generated
        chunks = enhanced_parser.chunker.preprocess_markdown(sample_content, "UHC-test.pdf")
        print(f"Generated {len(chunks)} chunks:")
        
        for i, chunk in enumerate(chunks[:5]):  # Show first 5 chunks
            print(f"   Chunk {i+1}: {chunk.content_type} (conf: {chunk.confidence_score:.2f})")
            print(f"      Hints: {chunk.extraction_hints}")
            print(f"      Content: {chunk.primary_content[:100]}...")
            print()
        
        # Now run the full enhanced parser
        enhanced_rules, chunks = enhanced_parser.parse_with_preprocessing(sample_content, "UHC-test.pdf")
        print(f"Enhanced parser: {len(enhanced_rules)} rules from {len(chunks)} chunks")
        
        # Analyze enhanced results
        enhanced_cpt_codes = set()
        enhanced_auth_required = 0
        enhanced_excluded_states = set()
        
        for rule in enhanced_rules:
            enhanced_cpt_codes.update(rule.cpt_codes)
            if hasattr(rule, 'excluded_states') and rule.excluded_states:
                enhanced_excluded_states.update(rule.excluded_states)
            
            if rule.auth_requirement.value == 'REQUIRED':
                enhanced_auth_required += 1
        
        print(f"   CPT codes found: {sorted(list(enhanced_cpt_codes))}")
        print(f"   Total CPT codes: {len(enhanced_cpt_codes)}")
        print(f"   Authorization REQUIRED: {enhanced_auth_required}")
        print(f"   States with exceptions: {sorted(list(enhanced_excluded_states))}")
        
    except Exception as e:
        print(f"Enhanced parser failed: {e}")
        import traceback
        traceback.print_exc()
        enhanced_rules = []
        enhanced_cpt_codes = set()
    
    # Analysis
    print("\nAnalysis:")
    
    if original_rules and enhanced_rules:
        print(f"   Rules: Original {len(original_rules)} vs Enhanced {len(enhanced_rules)}")
        print(f"   CPT codes: Original {len(original_cpt_codes)} vs Enhanced {len(enhanced_cpt_codes)}")
        
        # Find what the enhanced parser missed
        missed_codes = original_cpt_codes - enhanced_cpt_codes
        if missed_codes:
            print(f"   Enhanced parser missed: {sorted(list(missed_codes))}")
        
        # Find what the enhanced parser found extra
        extra_codes = enhanced_cpt_codes - original_cpt_codes
        if extra_codes:
            print(f"   Enhanced parser found extra: {sorted(list(extra_codes))}")
    
    # Debug chunk performance
    print(f"\nChunk Performance Analysis:")
    
    # Check how many chunks have CPT codes
    chunks_with_cpt = [c for c in chunks if 'cpt_codes' in c.extraction_hints and c.extraction_hints['cpt_codes']]
    print(f"   Chunks with CPT codes: {len(chunks_with_cpt)}/{len(chunks)}")
    
    # Check authorization rule chunks
    auth_chunks = [c for c in chunks if c.content_type == 'authorization_rule']
    print(f"   Authorization rule chunks: {len(auth_chunks)}")
    
    # Check geographic exception chunks
    geo_chunks = [c for c in chunks if c.content_type == 'geographic_exception']
    print(f"   Geographic exception chunks: {len(geo_chunks)}")
    
    print(f"\nReal data testing complete!")

if __name__ == "__main__":
    test_with_real_uhc_data()