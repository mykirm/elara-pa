#!/usr/bin/env python3
"""Compare rule parsing with marker vs pdfplumber outputs."""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add marker_env to path
sys.path.insert(0, '/Users/myrakirmani/Desktop/PA/pa-hypergraph-system/marker_env/lib/python3.11/site-packages')

from src.parsers.uhc_parser import convert_pdf_to_markdown, extract_tables_with_pdfplumber
from src.parsers.uhc_parser_rules import parse_markdown_to_rules

def test_rule_parsing_comparison():
    """Test rule parsing with both marker and pdfplumber outputs."""
    
    pdf_path = "data/UHC-Commercial-PA-Requirements-2025.pdf"
    
    print("=" * 80)
    print("Rule Parsing Comparison: Marker vs PDFPlumber")
    print("=" * 80)
    print(f"PDF: {pdf_path}")
    print(f"Start: {datetime.now().isoformat()}")
    print()
    
    # Check PDF exists
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    print(f"✅ PDF found: {Path(pdf_path).stat().st_size / 1024:.1f} KB")
    
    # Test 1: Use Marker (high quality)
    print("\n" + "=" * 60)
    print("TEST 1: MARKER EXTRACTION + RULE PARSING")
    print("=" * 60)
    
    try:
        print("🔄 Converting PDF with marker...")
        marker_text = convert_pdf_to_markdown(pdf_path)
        
        print(f"✅ Marker conversion successful")
        print(f"   Length: {len(marker_text):,} characters")
        print(f"   Lines: {len(marker_text.splitlines()):,}")
        
        print("\n🔄 Parsing rules from marker output...")
        marker_rules = parse_markdown_to_rules(marker_text, source_file=pdf_path)
        
        print(f"✅ Marker rule parsing completed")
        print(f"   Rules extracted: {len(marker_rules)}")
        
        # Analyze marker rules
        marker_stats = analyze_rules(marker_rules, "MARKER")
        
    except Exception as e:
        print(f"❌ Marker test failed: {e}")
        marker_rules = []
        marker_stats = {}
    
    # Test 2: Use PDFPlumber (fallback)
    print("\n" + "=" * 60)
    print("TEST 2: PDFPLUMBER EXTRACTION + RULE PARSING")
    print("=" * 60)
    
    try:
        print("🔄 Converting PDF with pdfplumber...")
        
        # Force pdfplumber extraction by simulating marker failure
        import pdfplumber
        text_content = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    text_content.append(f"# Page {page_num}\n\n{text}\n\n")
        
        pdfplumber_text = "\n".join(text_content)
        
        print(f"✅ PDFPlumber conversion successful")
        print(f"   Length: {len(pdfplumber_text):,} characters")
        print(f"   Lines: {len(pdfplumber_text.splitlines()):,}")
        
        print("\n🔄 Parsing rules from pdfplumber output...")
        pdfplumber_rules = parse_markdown_to_rules(pdfplumber_text, source_file=pdf_path + "_pdfplumber")
        
        print(f"✅ PDFPlumber rule parsing completed")
        print(f"   Rules extracted: {len(pdfplumber_rules)}")
        
        # Analyze pdfplumber rules
        pdfplumber_stats = analyze_rules(pdfplumber_rules, "PDFPLUMBER")
        
    except Exception as e:
        print(f"❌ PDFPlumber test failed: {e}")
        pdfplumber_rules = []
        pdfplumber_stats = {}
    
    # Comparison
    print("\n" + "=" * 80)
    print("COMPARISON RESULTS")
    print("=" * 80)
    
    print(f"Input Quality:")
    if 'marker_text' in locals():
        print(f"  📄 Marker text: {len(marker_text):,} chars, {len(marker_text.splitlines()):,} lines")
    if 'pdfplumber_text' in locals():
        print(f"  📄 PDFPlumber text: {len(pdfplumber_text):,} chars, {len(pdfplumber_text.splitlines()):,} lines")
    
    print(f"\nRule Extraction:")
    print(f"  🎯 Marker rules: {len(marker_rules)}")
    print(f"  🎯 PDFPlumber rules: {len(pdfplumber_rules)}")
    
    if marker_stats and pdfplumber_stats:
        print(f"\nRule Quality Comparison:")
        
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
    
    # Show sample rules from each
    if marker_rules:
        print(f"\n📋 Sample Marker Rules:")
        for i, rule in enumerate(marker_rules[:3]):
            print(f"  {i+1}. {rule.service or 'Unknown Service'} - {rule.auth_requirement.value}")
            print(f"     CPT: {rule.cpt_codes[:3]}{'...' if len(rule.cpt_codes) > 3 else ''}")
            print(f"     Category: {rule.category or 'None'}")
    
    if pdfplumber_rules:
        print(f"\n📋 Sample PDFPlumber Rules:")
        for i, rule in enumerate(pdfplumber_rules[:3]):
            print(f"  {i+1}. {rule.service or 'Unknown Service'} - {rule.auth_requirement.value}")
            print(f"     CPT: {rule.cpt_codes[:3]}{'...' if len(rule.cpt_codes) > 3 else ''}")
            print(f"     Category: {rule.category or 'None'}")
    
    print(f"\nOutput Files:")
    
    # Show processed rule files
    processed_files = list(Path("data/processed").glob("*_rules_*.json")) if Path("data/processed").exists() else []
    if processed_files:
        processed_files.sort(key=os.path.getctime, reverse=True)
        for file in processed_files[:4]:  # Show most recent files
            size_kb = file.stat().st_size / 1024
            mod_time = datetime.fromtimestamp(file.stat().st_mtime).strftime('%H:%M:%S')
            print(f"  📁 {file.name} ({size_kb:.1f} KB, {mod_time})")
    
    print(f"\nTest completed: {datetime.now().isoformat()}")


def analyze_rules(rules, source_name):
    """Analyze rule statistics for comparison."""
    stats = {
        'total_rules': len(rules),
        'required': 0,
        'conditional': 0,
        'not_required': 0,
        'notification_only': 0,
        'needs_llm': 0,
        'total_cpt_codes': 0,
        'categories': set(),
        'services': set()
    }
    
    for rule in rules:
        # Count auth requirements
        if rule.auth_requirement.value == 'REQUIRED':
            stats['required'] += 1
        elif rule.auth_requirement.value == 'CONDITIONAL':
            stats['conditional'] += 1
        elif rule.auth_requirement.value == 'NOT_REQUIRED':
            stats['not_required'] += 1
        elif rule.auth_requirement.value == 'NOTIFICATION_ONLY':
            stats['notification_only'] += 1
        
        # Count other attributes
        if rule.requires_llm_processing:
            stats['needs_llm'] += 1
        
        stats['total_cpt_codes'] += len(rule.cpt_codes)
        
        if rule.category:
            stats['categories'].add(rule.category)
        
        if rule.service:
            stats['services'].add(rule.service)
    
    # Convert sets to lists for JSON serialization later
    stats['categories'] = list(stats['categories'])
    stats['services'] = list(stats['services'])
    
    print(f"\n📊 {source_name} Rule Analysis:")
    print(f"   Total Rules: {stats['total_rules']}")
    print(f"   Auth Types - Required: {stats['required']}, Conditional: {stats['conditional']}")
    print(f"   CPT Codes: {stats['total_cpt_codes']}")
    print(f"   Categories: {len(stats['categories'])}")
    print(f"   Services: {len(stats['services'])}")
    print(f"   Needs LLM: {stats['needs_llm']}")
    
    return stats


if __name__ == "__main__":
    test_rule_parsing_comparison()