#!/usr/bin/env python3
"""
Comprehensive test using the actual UHC Commercial PA Requirements document.

This test shows:
1. What exactly is being extracted from real UHC data
2. Complex cases and edge cases
3. How to manually verify the results
4. Comparison between different extraction methods
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.models import Rule, AuthRequirement, RuleType
    from src.parsers.enhanced_rule_parser import EnhancedRuleParser
    from src.preprocessing.intelligent_chunker import BasicIntelligentChunker
    from src.parsers.payer_rules.uhc_rules import parse_markdown_to_rules
except ImportError:
    print("Import error - running from project root")
    from models import Rule, AuthRequirement, RuleType
    from parsers.enhanced_rule_parser import EnhancedRuleParser
    from preprocessing.intelligent_chunker import BasicIntelligentChunker
    from parsers.payer_rules.uhc_rules import parse_markdown_to_rules


class UHCDocumentTester:
    """Comprehensive tester for UHC document processing"""
    
    def __init__(self):
        self.enhanced_parser = EnhancedRuleParser()
        self.basic_chunker = BasicIntelligentChunker()
        
        # Sample UHC content from the actual document
        self.uhc_sample_data = """
# Prior Authorization Requirements for UnitedHealthcare

Effective Jan. 1, 2025

## General information

This list contains prior authorization review requirements for participating UnitedHealthcare commercial plan health care professionals providing inpatient and outpatient services.

## Procedures and Services

### Arthroplasty
Prior authorization required.

CPT Codes:
23470, 23472, 23473, 23474
24360, 24361, 24362, 24363
24365, 24370, 24371, 25441
25442, 25443, 25444, 25446
27120, 27125, 27130, 27132
27437, 27438, 27440, 27441
27447, 27486, 27487, 27700

### Arthroscopy
Prior authorization required for all states.

CPT Codes requiring PA:
29826, 29843, 29871

Additional codes with site of service review (except Alaska, Massachusetts, Puerto Rico, Rhode Island, Texas, Utah, Virgin Islands, Wisconsin):
29805, 29806, 29807, 29819
29820, 29821, 29822, 29823
29881, 29882, 29883, 29884

### Bariatric surgery
Prior authorization required.
Center of Excellence requirement for coverage.

CPT Codes:
43644, 43645, 43659, 43770
43771, 43772, 43773, 43774
43842, 43843, 43845, 43846

Notification/prior authorization required for diagnosis codes:
E66.01, E66.09, E66.1-E66.3, E66.8, E66.9, Z68.1, Z68.20-Z68.22

### Breast reconstruction (non-mastectomy)
Prior authorization required.

CPT Codes:
15771, 19300, 19316, 19318
19325, 19328, 19330, 19340

Notification/prior authorization NOT required for diagnosis codes:
C50.019, C50.011, C50.012, C50.111
C50.411, C50.412, C50.419, C50.511

### Behavioral health services
Many benefit plans only provide coverage through designated behavioral health network.
Call member ID card number for mental health referrals.

### Therapeutic radiopharmaceuticals
Prior authorization required.

HCPCS Codes:
A9513, A9590, A9606, A9607, A9699

Submit requests via Provider Portal at UHCprovider.com
"""

    def test_complex_cases(self) -> Dict[str, Any]:
        """Test complex cases from UHC document"""
        
        print("🔬 Testing Complex Cases from UHC Document")
        print("=" * 80)
        
        results = {
            'test_cases': {},
            'verification_guide': {},
            'extraction_comparison': {}
        }
        
        # Test Case 1: State Exceptions (Arthroscopy)
        print("\n📍 Test Case 1: State Exceptions in Arthroscopy")
        print("-" * 50)
        
        arthroscopy_text = """
        ### Arthroscopy
        Prior authorization required for all states.
        
        Additional codes with site of service review except in Alaska, Massachusetts, Puerto Rico, Rhode Island, Texas, Utah, the Virgin Islands and Wisconsin:
        29805, 29806, 29807, 29819, 29820, 29821
        """
        
        # Parse with enhanced parser
        enhanced_rules, chunks = self.enhanced_parser.parse_with_preprocessing(arthroscopy_text, "test_arthroscopy")
        
        # Show what was extracted
        print(f"✓ Enhanced parser found {len(enhanced_rules)} rules")
        for i, rule in enumerate(enhanced_rules, 1):
            print(f"  Rule {i}:")
            print(f"    - CPT Codes: {rule.cpt_codes}")
            print(f"    - Auth Required: {rule.auth_requirement}")
            print(f"    - Excluded States: {rule.excluded_states}")
            print(f"    - Clinical Criteria: {rule.clinical_criteria}")
        
        results['test_cases']['state_exceptions'] = {
            'input': arthroscopy_text,
            'rules_found': len(enhanced_rules),
            'expected_excluded_states': ['AK', 'MA', 'PR', 'RI', 'TX', 'UT', 'VI', 'WI'],
            'actual_excluded_states': enhanced_rules[0].excluded_states if enhanced_rules else [],
            'manual_verification': "Check if Alaska, Massachusetts, Puerto Rico, Rhode Island, Texas, Utah, Virgin Islands, Wisconsin are detected as excluded"
        }
        
        # Test Case 2: Diagnosis Code Exceptions (Breast Reconstruction)
        print("\n📍 Test Case 2: Diagnosis Code Exceptions")
        print("-" * 50)
        
        breast_recon_text = """
        ### Breast reconstruction (non-mastectomy)
        Prior authorization required.
        
        CPT Codes: 15771, 19300, 19316, 19318
        
        Notification/prior authorization NOT required for the following diagnosis codes:
        C50.019, C50.011, C50.012, C50.111
        C50.411, C50.412, C50.419, C50.511
        """
        
        enhanced_rules_2, chunks_2 = self.enhanced_parser.parse_with_preprocessing(breast_recon_text, "test_breast")
        
        print(f"✓ Enhanced parser found {len(enhanced_rules_2)} rules")
        for i, rule in enumerate(enhanced_rules_2, 1):
            print(f"  Rule {i}:")
            print(f"    - CPT Codes: {rule.cpt_codes}")
            print(f"    - ICD Codes: {rule.icd_codes}")
            print(f"    - Auth Required: {rule.auth_requirement}")
            print(f"    - Narrative Text: {rule.narrative_text}")
        
        results['test_cases']['diagnosis_exceptions'] = {
            'input': breast_recon_text,
            'rules_found': len(enhanced_rules_2),
            'expected_icd_codes': ['C50.019', 'C50.011', 'C50.012', 'C50.111', 'C50.411', 'C50.412', 'C50.419', 'C50.511'],
            'actual_icd_codes': enhanced_rules_2[0].icd_codes if enhanced_rules_2 else [],
            'manual_verification': "Check if breast cancer diagnosis codes are extracted and marked as exceptions"
        }
        
        # Test Case 3: Complex Authorization Logic (Bariatric Surgery)
        print("\n📍 Test Case 3: Complex Authorization Logic")
        print("-" * 50)
        
        bariatric_text = """
        ### Bariatric surgery
        Prior authorization required.
        Center of Excellence requirement for coverage.
        In certain situations, bariatric surgery isn't covered by some benefit plans.
        
        CPT Codes: 43644, 43645, 43659, 43770, 43771
        
        Notification/prior authorization required for diagnosis codes:
        E66.01, E66.09, E66.1-E66.3, E66.8, E66.9, Z68.1, Z68.20-Z68.22
        """
        
        enhanced_rules_3, chunks_3 = self.enhanced_parser.parse_with_preprocessing(bariatric_text, "test_bariatric")
        
        print(f"✓ Enhanced parser found {len(enhanced_rules_3)} rules")
        for i, rule in enumerate(enhanced_rules_3, 1):
            print(f"  Rule {i}:")
            print(f"    - CPT Codes: {rule.cpt_codes}")
            print(f"    - Clinical Criteria: {rule.clinical_criteria}")
            print(f"    - Narrative Text: {rule.narrative_text}")
            print(f"    - Requires LLM: {rule.requires_llm_processing}")
        
        results['test_cases']['complex_authorization'] = {
            'input': bariatric_text,
            'rules_found': len(enhanced_rules_3),
            'expected_clinical_criteria': "Center of Excellence",
            'actual_clinical_criteria': enhanced_rules_3[0].clinical_criteria if enhanced_rules_3 else None,
            'manual_verification': "Check if Center of Excellence requirement is captured"
        }
        
        # Test Case 4: Full Document Processing
        print("\n📍 Test Case 4: Full Document Sample Processing")
        print("-" * 50)
        
        enhanced_rules_full, chunks_full = self.enhanced_parser.parse_with_preprocessing(self.uhc_sample_data, "uhc_sample")
        
        print(f"✓ Enhanced parser found {len(enhanced_rules_full)} rules")
        print(f"✓ Created {len(chunks_full)} processed chunks")
        
        # Analyze chunk types
        chunk_types = {}
        for chunk in chunks_full:
            chunk_type = chunk.content_type
            if chunk_type not in chunk_types:
                chunk_types[chunk_type] = 0
            chunk_types[chunk_type] += 1
        
        print(f"✓ Chunk distribution:")
        for chunk_type, count in chunk_types.items():
            print(f"    - {chunk_type}: {count}")
        
        # Show sample rules
        print(f"\n✓ Sample extracted rules:")
        for i, rule in enumerate(enhanced_rules_full[:3], 1):
            print(f"  Rule {i}: {rule.service} - {len(rule.cpt_codes)} CPT codes - {rule.auth_requirement}")
        
        results['test_cases']['full_document'] = {
            'total_rules': len(enhanced_rules_full),
            'total_chunks': len(chunks_full),
            'chunk_distribution': chunk_types,
            'sample_rules': [
                {
                    'service': rule.service,
                    'cpt_count': len(rule.cpt_codes),
                    'auth_requirement': rule.auth_requirement.value if rule.auth_requirement else None
                } for rule in enhanced_rules_full[:5]
            ]
        }
        
        return results
    
    def create_verification_guide(self) -> Dict[str, str]:
        """Create manual verification guide"""
        
        return {
            'cpt_codes': """
            Manual Verification for CPT Codes:
            1. Check UHC PDF pages 1-32 for procedure codes
            2. Verify 5-digit numeric codes are captured (e.g., 23470, 27447)
            3. Ensure codes in table format are extracted correctly
            4. Look for missing codes in multi-column layouts
            """,
            
            'state_exceptions': """
            Manual Verification for State Exceptions:
            1. Search PDF for text like "except in [states]" or "excluding [states]"
            2. Look for phrases like "all states except" or "limited to"
            3. Verify state abbreviations are correctly identified
            4. Check geographic restriction patterns
            """,
            
            'authorization_types': """
            Manual Verification for Authorization Types:
            1. Look for "Prior authorization required" → REQUIRED
            2. Look for "No prior authorization" → NOT_REQUIRED  
            3. Look for "Notification only" → NOTIFICATION_ONLY
            4. Complex cases may need → CONDITIONAL
            """,
            
            'diagnosis_codes': """
            Manual Verification for Diagnosis Codes:
            1. Look for ICD-10 patterns (letter + 2 digits + optional decimal)
            2. Check "diagnosis codes" sections in procedures
            3. Verify exception lists ("NOT required for...")
            4. Look for ranges like "E66.1-E66.3"
            """,
            
            'special_requirements': """
            Manual Verification for Special Requirements:
            1. Look for "Center of Excellence" requirements
            2. Check for network restrictions
            3. Find coverage limitations or exclusions
            4. Identify site-of-service requirements
            """
        }
    
    def compare_extraction_methods(self) -> Dict[str, Any]:
        """Compare different extraction approaches"""
        
        print("\n🔄 Comparing Extraction Methods")
        print("=" * 50)
        
        test_text = """
        ### Arthroplasty
        Prior authorization required.
        23470, 23472, 23473, 23474
        24360, 24361, 24362, 24363
        27447, 27486, 27487, 27700
        """
        
        # Method 1: Enhanced parser with chunking
        enhanced_rules, chunks = self.enhanced_parser.parse_with_preprocessing(test_text, "comparison_test")
        
        # Method 2: Basic line-by-line parsing
        try:
            basic_rules = parse_markdown_to_rules(test_text, "comparison_test")
        except:
            basic_rules = []
        
        print(f"Enhanced Parser: {len(enhanced_rules)} rules")
        print(f"Basic Parser: {len(basic_rules)} rules")
        
        comparison = {
            'enhanced': {
                'rules_count': len(enhanced_rules),
                'chunks_created': len(chunks),
                'cpt_codes_found': sum(len(r.cpt_codes) for r in enhanced_rules),
                'context_preserved': any(c.content_type == 'authorization_rule' for c in chunks)
            },
            'basic': {
                'rules_count': len(basic_rules),
                'cpt_codes_found': sum(len(r.cpt_codes) for r in basic_rules),
                'line_by_line': True
            }
        }
        
        print(f"Enhanced: {comparison['enhanced']['cpt_codes_found']} CPT codes")
        print(f"Basic: {comparison['basic']['cpt_codes_found']} CPT codes")
        
        return comparison
    
    def save_test_results(self, results: Dict[str, Any], output_dir: str = "test_results"):
        """Save test results for review"""
        
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save detailed results
        results_file = f"{output_dir}/uhc_test_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save verification guide
        guide_file = f"{output_dir}/verification_guide_{timestamp}.md"
        verification_guide = self.create_verification_guide()
        
        with open(guide_file, 'w') as f:
            f.write("# UHC Document Verification Guide\n\n")
            for section, content in verification_guide.items():
                f.write(f"## {section.replace('_', ' ').title()}\n\n")
                f.write(content.strip() + "\n\n")
        
        print(f"\n💾 Test results saved:")
        print(f"   📄 Results: {results_file}")
        print(f"   📋 Guide: {guide_file}")
        
        return results_file, guide_file


def main():
    """Run comprehensive UHC document tests"""
    
    print("🧪 UHC Document Comprehensive Testing")
    print("=" * 80)
    print("Testing real UHC Commercial PA Requirements document")
    print("Source: https://www.uhcprovider.com/.../UHC-Commercial-Advance-Notification-PA-Requirements-1-1-2025.pdf")
    print()
    
    tester = UHCDocumentTester()
    
    # Run complex case tests
    test_results = tester.test_complex_cases()
    
    # Compare extraction methods
    comparison_results = tester.compare_extraction_methods()
    test_results['extraction_comparison'] = comparison_results
    
    # Create verification guide
    verification_guide = tester.create_verification_guide()
    test_results['verification_guide'] = verification_guide
    
    # Save results
    results_file, guide_file = tester.save_test_results(test_results)
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    print(f"✓ State exceptions test: {'PASS' if test_results['test_cases']['state_exceptions']['rules_found'] > 0 else 'FAIL'}")
    print(f"✓ Diagnosis exceptions test: {'PASS' if test_results['test_cases']['diagnosis_exceptions']['rules_found'] > 0 else 'FAIL'}")
    print(f"✓ Complex authorization test: {'PASS' if test_results['test_cases']['complex_authorization']['rules_found'] > 0 else 'FAIL'}")
    print(f"✓ Full document test: {test_results['test_cases']['full_document']['total_rules']} rules extracted")
    
    print(f"\n🔍 Manual Verification Steps:")
    print(f"1. Open the UHC PDF document")
    print(f"2. Compare extracted rules with source pages")
    print(f"3. Check CPT codes against procedure tables")
    print(f"4. Verify state exceptions in geographic sections")
    print(f"5. Review diagnosis code exceptions")
    print(f"6. Validate special requirements and coverage notes")
    
    print(f"\n📋 For detailed verification instructions, see: {guide_file}")


if __name__ == "__main__":
    main()
