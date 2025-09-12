#!/usr/bin/env python3
"""Main script to process Prior Authorization documents into hypergraph format."""

import sys
import os
from pathlib import Path
import argparse
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Add marker environment to path
sys.path.insert(0, '/Users/myrakirmani/Desktop/PA/pa-hypergraph-system/marker_env/lib/python3.11/site-packages')

from src.parsers import (
    convert_pdf_to_markdown,
    extract_tables_with_pdfplumber,
    parse_markdown_to_rules,
    save_processed_rules
)


def process_pa_document(pdf_path: str, output_dir: str = "data/processed", use_marker: bool = True):
    """Process a PA document through the full pipeline.
    
    Args:
        pdf_path: Path to the PA PDF document
        output_dir: Directory for output files
        use_marker: Whether to use marker (True) or pdfplumber (False)
    
    Returns:
        List of Rule objects
    """
    print(f"{'=' * 80}")
    print(f"Processing PA Document: {Path(pdf_path).name}")
    print(f"{'=' * 80}")
    print(f"Method: {'Marker (high-quality)' if use_marker else 'PDFPlumber (fallback)'}")
    print(f"Output: {output_dir}")
    print()
    
    # Step 1: Extract text from PDF
    if use_marker:
        print("🔄 Extracting with marker...")
        try:
            text = convert_pdf_to_markdown(pdf_path)
            print(f"✅ Extracted {len(text):,} characters")
        except Exception as e:
            print(f"⚠️  Marker failed: {e}, falling back to pdfplumber")
            use_marker = False
    
    if not use_marker:
        print("🔄 Extracting with pdfplumber...")
        import pdfplumber
        text_content = []
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()
                if page_text:
                    text_content.append(f"# Page {page_num}\n\n{page_text}\n\n")
        text = "\n".join(text_content)
        print(f"✅ Extracted {len(text):,} characters")
    
    # Step 2: Extract tables (always useful for validation)
    print("\n🔄 Extracting tables...")
    tables = extract_tables_with_pdfplumber(pdf_path)
    print(f"✅ Found {len(tables)} tables")
    
    # Step 3: Parse rules
    print("\n🔄 Parsing rules...")
    rules = parse_markdown_to_rules(text, source_file=Path(pdf_path).name)
    print(f"✅ Extracted {len(rules)} rules")
    
    # Step 4: Analyze results
    print("\n📊 Analysis:")
    
    # Count by auth requirement
    auth_counts = {}
    for rule in rules:
        auth_type = rule.auth_requirement.value
        auth_counts[auth_type] = auth_counts.get(auth_type, 0) + 1
    
    for auth_type, count in auth_counts.items():
        print(f"  {auth_type}: {count} rules")
    
    # Count CPT codes
    total_cpt = sum(len(rule.cpt_codes) for rule in rules)
    print(f"  Total CPT codes: {total_cpt}")
    
    # Count categories
    categories = set(rule.category for rule in rules if rule.category)
    print(f"  Categories: {len(categories)}")
    
    # Count rules needing LLM
    llm_needed = sum(1 for rule in rules if rule.requires_llm_processing)
    print(f"  Rules needing LLM: {llm_needed}")
    
    print(f"\n✅ Processing complete!")
    print(f"   Check {output_dir} for output files")
    
    return rules


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Process Prior Authorization PDF documents into structured rules"
    )
    parser.add_argument(
        "pdf_path",
        help="Path to the PA PDF document"
    )
    parser.add_argument(
        "--output-dir",
        default="data/processed",
        help="Directory for output files (default: data/processed)"
    )
    parser.add_argument(
        "--use-pdfplumber",
        action="store_true",
        help="Use pdfplumber instead of marker for extraction"
    )
    parser.add_argument(
        "--page-limit",
        type=int,
        help="Limit processing to first N pages"
    )
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.pdf_path):
        print(f"❌ Error: File not found: {args.pdf_path}")
        sys.exit(1)
    
    # Process document
    use_marker = not args.use_pdfplumber
    rules = process_pa_document(args.pdf_path, args.output_dir, use_marker)
    
    # Save summary
    summary_path = Path(args.output_dir) / f"{Path(args.pdf_path).stem}_summary.json"
    summary = {
        "source_file": args.pdf_path,
        "processed_at": datetime.now().isoformat(),
        "method": "marker" if use_marker else "pdfplumber",
        "total_rules": len(rules),
        "auth_types": {
            auth_type: sum(1 for r in rules if r.auth_requirement.value == auth_type)
            for auth_type in ["REQUIRED", "CONDITIONAL", "NOT_REQUIRED", "NOTIFICATION_ONLY"]
        },
        "total_cpt_codes": sum(len(r.cpt_codes) for r in rules),
        "categories": list(set(r.category for r in rules if r.category))
    }
    
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📄 Summary saved to: {summary_path}")


if __name__ == "__main__":
    main()