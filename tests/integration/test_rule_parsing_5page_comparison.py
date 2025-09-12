#!/usr/bin/env python3
"""Compare rule parsing with marker vs pdfplumber on first 5 pages only."""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add marker_env to path
sys.path.insert(0, '/Users/myrakirmani/Desktop/PA/pa-hypergraph-system/marker_env/lib/python3.11/site-packages')

from src.parsers.uhc_parser_rules import parse_markdown_to_rules

def test_5page_rule_parsing_comparison():
    """Test rule parsing with both marker and pdfplumber on first 5 pages only."""
    
    pdf_path = "data/UHC-Commercial-PA-Requirements-2025.pdf"
    
    print("=" * 80)
    print("5-Page Rule Parsing Comparison: Marker vs PDFPlumber")
    print("=" * 80)
    print(f"PDF: {pdf_path}")
    print(f"Start: {datetime.now().isoformat()}")
    print()
    
    # Test 1: Use existing marker output (5 pages)
    print("=" * 60)
    print("TEST 1: MARKER OUTPUT (5 PAGES)")
    print("=" * 60)
    
    marker_files = list(Path("data/raw").glob("marker_5pages_*/*/UHC-Commercial-PA-Requirements-2025.md"))
    
    if marker_files:
        marker_file = marker_files[0]  # Use the most recent one
        print(f"📁 Using existing marker output: {marker_file}")
        
        with open(marker_file, 'r', encoding='utf-8') as f:
            marker_text = f.read()
        
        print(f"   Length: {len(marker_text):,} characters")
        print(f"   Lines: {len(marker_text.splitlines()):,}")
        
        print("\n🔄 Parsing rules from marker output...")
        marker_rules = parse_markdown_to_rules(marker_text, source_file="UHC-5pages-marker")
        
        print(f"✅ Marker rule parsing completed")
        print(f"   Rules extracted: {len(marker_rules)}")
        
        # Analyze marker rules
        marker_stats = analyze_rules(marker_rules, "MARKER")
        
    else:
        print("❌ No marker 5-page output found. Run test_marker_5_pages.py first.")
        marker_rules = []
        marker_stats = {}
        marker_text = ""
    
    # Test 2: PDFPlumber (first 5 pages only)
    print("\n" + "=" * 60)
    print("TEST 2: PDFPLUMBER OUTPUT (5 PAGES)")
    print("=" * 60)
    
    try:
        print("🔄 Extracting first 5 pages with pdfplumber...")
        
        import pdfplumber
        text_content = []
        
        with pdfplumber.open(pdf_path) as pdf:
            # Only process first 5 pages
            for page_num in range(min(5, len(pdf.pages))):
                page = pdf.pages[page_num]
                text = page.extract_text()
                if text:
                    text_content.append(f"# Page {page_num + 1}\n\n{text}\n\n")
        
        pdfplumber_text = "\n".join(text_content)
        
        print(f"✅ PDFPlumber extraction successful")
        print(f"   Length: {len(pdfplumber_text):,} characters")
        print(f"   Lines: {len(pdfplumber_text.splitlines()):,}")
        
        print("\n🔄 Parsing rules from pdfplumber output...")
        pdfplumber_rules = parse_markdown_to_rules(pdfplumber_text, source_file="UHC-5pages-pdfplumber")
        
        print(f"✅ PDFPlumber rule parsing completed")
        print(f"   Rules extracted: {len(pdfplumber_rules)}")
        
        # Analyze pdfplumber rules
        pdfplumber_stats = analyze_rules(pdfplumber_rules, "PDFPLUMBER")
        
    except Exception as e:
        print(f"❌ PDFPlumber test failed: {e}")
        pdfplumber_rules = []
        pdfplumber_stats = {}
        pdfplumber_text = ""
    
    # Side-by-side text quality comparison
    print("\n" + "=" * 80)
    print("TEXT QUALITY COMPARISON")
    print("=" * 80)
    
    if marker_text and pdfplumber_text:
        print("📄 First 500 characters from each:")
        print("\nMARKER:")
        print("─" * 40)
        marker_preview = marker_text[:500].replace('\n', '\n   ')
        print(f"   {marker_preview}...")
        
        print("\nPDFPLUMBER:")
        print("─" * 40)
        pdfplumber_preview = pdfplumber_text[:500].replace('\n', '\n   ')
        print(f"   {pdfplumber_preview}...")
        
        # Count structural elements
        marker_headers = len([line for line in marker_text.split('\n') if line.startswith('#')])
        marker_tables = len([line for line in marker_text.split('\n') if '|' in line and len(line.split('|')) > 2])
        
        pdfplumber_headers = len([line for line in pdfplumber_text.split('\n') if line.startswith('#')])
        pdfplumber_tables = len([line for line in pdfplumber_text.split('\n') if '|' in line and len(line.split('|')) > 2])
        
        print(f"\n📊 Structure Analysis:")
        print(f"   Headers - Marker: {marker_headers}, PDFPlumber: {pdfplumber_headers}")
        print(f"   Table rows - Marker: {marker_tables}, PDFPlumber: {pdfplumber_tables}")
    
    # Comparison
    print("\n" + "=" * 80)
    print("RULE EXTRACTION COMPARISON")
    print("=" * 80)
    
    print(f"Input Quality:")
    if marker_text:
        print(f"  📄 Marker text: {len(marker_text):,} chars, {len(marker_text.splitlines()):,} lines")
    if pdfplumber_text:
        print(f"  📄 PDFPlumber text: {len(pdfplumber_text):,} chars, {len(pdfplumber_text.splitlines()):,} lines")
    
    print(f"\nRule Extraction Results:")
    print(f"  🎯 Marker rules: {len(marker_rules)}")
    print(f"  🎯 PDFPlumber rules: {len(pdfplumber_rules)}")
    
    if marker_stats and pdfplumber_stats:
        print(f"\nDetailed Comparison:")
        
        print(f"  Authorization Requirements:")
        print(f"    Marker - Required: {marker_stats.get('required', 0)}, Conditional: {marker_stats.get('conditional', 0)}")
        print(f"    PDFPlumber - Required: {pdfplumber_stats.get('required', 0)}, Conditional: {pdfplumber_stats.get('conditional', 0)}")
        
        print(f"  CPT Codes Found:")
        print(f"    Marker: {marker_stats.get('total_cpt_codes', 0)}")
        print(f"    PDFPlumber: {pdfplumber_stats.get('total_cpt_codes', 0)}")
        
        print(f"  Categories Identified:")
        print(f"    Marker: {len(marker_stats.get('categories', []))}")
        print(f"    PDFPlumber: {len(pdfplumber_stats.get('categories', []))}")
        
        print(f"  Complex Rules Needing LLM:")
        print(f"    Marker: {marker_stats.get('needs_llm', 0)}")
        print(f"    PDFPlumber: {pdfplumber_stats.get('needs_llm', 0)}")
        
        print(f"  Average Confidence:")
        print(f"    Marker: {marker_stats.get('avg_confidence', 0):.2f}")
        print(f"    PDFPlumber: {pdfplumber_stats.get('avg_confidence', 0):.2f}")
    
    # Show sample rules from each
    if marker_rules:
        print(f"\n📋 Sample Marker Rules:")
        for i, rule in enumerate(marker_rules[:3]):
            print(f"  {i+1}. Service: {rule.service or 'Unknown'}")
            print(f"     Auth: {rule.auth_requirement.value}")
            print(f"     CPT: {rule.cpt_codes[:3]}{'...' if len(rule.cpt_codes) > 3 else ''}")
            print(f"     Category: {rule.category or 'None'}")
            print(f"     Confidence: {rule.confidence_score}")
    
    if pdfplumber_rules:
        print(f"\n📋 Sample PDFPlumber Rules:")
        for i, rule in enumerate(pdfplumber_rules[:3]):
            print(f"  {i+1}. Service: {rule.service or 'Unknown'}")
            print(f"     Auth: {rule.auth_requirement.value}")
            print(f"     CPT: {rule.cpt_codes[:3]}{'...' if len(rule.cpt_codes) > 3 else ''}")
            print(f"     Category: {rule.category or 'None'}")
            print(f"     Confidence: {rule.confidence_score}")
    
    print(f"\n💡 Recommendation:")
    if len(marker_rules) > len(pdfplumber_rules):
        print("   Marker extracted more rules - likely better structure recognition")
    elif len(pdfplumber_rules) > len(marker_rules):
        print("   PDFPlumber extracted more rules - may be catching different patterns")
    else:
        print("   Both methods found similar number of rules - check quality metrics")
    
    print(f"\nTest completed: {datetime.now().isoformat()}")


def analyze_rules(rules, source_name):
    """Analyze rule statistics for comparison."""
    if not rules:
        return {}
    
    stats = {
        'total_rules': len(rules),
        'required': 0,
        'conditional': 0,
        'not_required': 0,
        'notification_only': 0,
        'needs_llm': 0,
        'total_cpt_codes': 0,
        'categories': set(),
        'services': set(),
        'confidence_scores': []
    }
    
    for rule in rules:
        # Count auth requirements
        auth_val = rule.auth_requirement.value
        if auth_val == 'REQUIRED':
            stats['required'] += 1
        elif auth_val == 'CONDITIONAL':
            stats['conditional'] += 1
        elif auth_val == 'NOT_REQUIRED':
            stats['not_required'] += 1
        elif auth_val == 'NOTIFICATION_ONLY':
            stats['notification_only'] += 1
        
        # Count other attributes
        if rule.requires_llm_processing:
            stats['needs_llm'] += 1
        
        stats['total_cpt_codes'] += len(rule.cpt_codes)
        
        if rule.category:
            stats['categories'].add(rule.category)
        
        if rule.service:
            stats['services'].add(rule.service)
        
        if rule.confidence_score:
            stats['confidence_scores'].append(rule.confidence_score)
    
    # Calculate average confidence
    stats['avg_confidence'] = sum(stats['confidence_scores']) / len(stats['confidence_scores']) if stats['confidence_scores'] else 0
    
    # Convert sets to lists for JSON serialization later
    stats['categories'] = list(stats['categories'])
    stats['services'] = list(stats['services'])
    
    print(f"\n📊 {source_name} Analysis:")
    print(f"   Total Rules: {stats['total_rules']}")
    print(f"   Auth Types - Required: {stats['required']}, Conditional: {stats['conditional']}")
    print(f"   CPT Codes: {stats['total_cpt_codes']}")
    print(f"   Categories: {len(stats['categories'])}")
    print(f"   Services: {len(stats['services'])}")
    print(f"   Needs LLM: {stats['needs_llm']}")
    print(f"   Avg Confidence: {stats['avg_confidence']:.2f}")
    
    return stats


if __name__ == "__main__":
    test_5page_rule_parsing_comparison()