#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the BasicIntelligentChunker with sample UHC data"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from preprocessing.intelligent_chunker import BasicIntelligentChunker, ProcessedChunk

def test_chunker_basic():
    """Test basic chunker functionality"""
    print("Testing BasicIntelligentChunker...")
    
    chunker = BasicIntelligentChunker()
    
    # Sample UHC content for testing
    test_content = """
# Orthopedic Procedures

## Arthroscopic Procedures
Prior authorization is required for the following procedures:

CPT codes 29826, 29827, 29828 require prior authorization.

## Geographic Exceptions
The following states are excluded from prior authorization requirements:
- California (CA) 
- New York (NY)
- Texas (TX)

Exception: CPT codes 29805-29825 do not require prior authorization.

## Diagnostic Imaging
MRI procedures (CPT codes 72148, 72149) require prior authorization when used for chronic pain diagnosis (ICD M79.3).

Notification only required for emergency procedures in all states except FL.
"""
    
    # Process the content
    chunks = chunker.preprocess_markdown(test_content, "test_uhc.pdf")
    
    print(f"Generated {len(chunks)} chunks")
    
    # Display results
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i+1} ---")
        print(f"Content Type: {chunk.content_type}")
        print(f"Confidence: {chunk.confidence_score:.2f}")
        print(f"Section Hierarchy: {chunk.section_hierarchy}")
        print(f"Extraction Hints: {chunk.extraction_hints}")
        print(f"Content Length: {len(chunk.primary_content)} chars")
        if chunk.primary_content:
            print(f"Content Preview: {chunk.primary_content[:100]}...")
    
    # Get classification stats
    stats = chunker.get_classification_stats(chunks)
    print(f"\nClassification Statistics:")
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Content types: {stats['content_types']}")
    print(f"Average confidence: {stats['average_confidence']:.2f}")
    print(f"High confidence chunks: {stats['high_confidence_chunks']}")
    print(f"Extraction hints found: {stats['extraction_hints_found']}")
    
    return chunks

def test_cpt_code_extraction():
    """Test CPT code extraction accuracy"""
    print("\nTesting CPT Code Extraction...")
    
    chunker = BasicIntelligentChunker()
    
    test_cases = [
        ("CPT codes 29826, 29827, 29828 require prior authorization", ["29826", "29827", "29828"]),
        ("Procedures 72148-72149 need PA", ["72148", "72149"]),  # Range
        ("HCPCS codes A0425, B4150 are covered", ["A0425", "B4150"]),
        ("Code range 29805-29825 excluded", ["29805", "29825"]),
        ("No codes in this text", [])
    ]
    
    for text, expected_codes in test_cases:
        chunks = chunker.preprocess_markdown(text, "test.pdf")
        
        # Extract all CPT codes found
        found_codes = []
        for chunk in chunks:
            if 'cpt_codes' in chunk.extraction_hints:
                found_codes.extend(chunk.extraction_hints['cpt_codes'])
        
        print(f"Text: {text[:50]}...")
        print(f"Expected: {expected_codes}")
        print(f"Found: {found_codes}")
        
        # Check if we found the expected codes (allowing for ranges)
        success = True
        for expected in expected_codes:
            if expected not in found_codes:
                # Check if it's part of a range
                range_found = any(expected in code for code in found_codes if 'RANGE_' in code)
                if not range_found:
                    success = False
                    break
        
        print(f"Result: {'PASS' if success else 'FAIL'}\n")

def test_auth_requirement_detection():
    """Test authorization requirement language detection"""
    print("Testing Authorization Requirement Detection...")
    
    chunker = BasicIntelligentChunker()
    
    test_cases = [
        ("Prior authorization required for CPT 29826", "REQUIRED"),
        ("CPT 29827 requires prior auth", "REQUIRED"), 
        ("No prior authorization needed for 72148", "NOT_REQUIRED"),
        ("CPT 29825 is not required", "NOT_REQUIRED"),
        ("Notification only for emergency procedures", None),  # Should be detected as notification
        ("Geographic exception: CA excluded from PA requirements", "NOT_REQUIRED")  # Exception context
    ]
    
    for text, expected_auth in test_cases:
        chunks = chunker.preprocess_markdown(text, "test.pdf")
        
        found_auth = None
        for chunk in chunks:
            if 'auth_requirement' in chunk.extraction_hints:
                found_auth = chunk.extraction_hints['auth_requirement']
                break
        
        print(f"Text: {text}")
        print(f"Expected: {expected_auth}")
        print(f"Found: {found_auth}")
        
        success = (found_auth == expected_auth)
        print(f"Result: {'PASS' if success else 'FAIL'}\n")

def test_state_detection():
    """Test state abbreviation detection"""
    print("Testing State Detection...")
    
    chunker = BasicIntelligentChunker()
    
    test_cases = [
        ("Exception for California (CA) and New York (NY)", ["CA", "NY"]),
        ("Texas (TX) has different requirements", ["TX"]),
        ("All states except FL require notification", ["FL"]),
        ("No geographic restrictions mentioned", [])
    ]
    
    for text, expected_states in test_cases:
        chunks = chunker.preprocess_markdown(text, "test.pdf")
        
        found_states = []
        for chunk in chunks:
            if 'states' in chunk.extraction_hints:
                found_states.extend(chunk.extraction_hints['states'])
        
        print(f"Text: {text}")
        print(f"Expected: {expected_states}")
        print(f"Found: {found_states}")
        
        success = set(found_states) == set(expected_states)
        print(f"Result: {'PASS' if success else 'FAIL'}\n")

def test_content_classification():
    """Test content type classification accuracy"""
    print("Testing Content Classification...")
    
    chunker = BasicIntelligentChunker()
    
    test_cases = [
        ("Prior authorization required for CPT 29826, 29827", "authorization_rule"),
        ("Geographic exception: CA and NY excluded", "geographic_exception"),
        ("CPT codes 29805, 29806, 29807, 29808", "procedure_list"),
        ("General information about orthopedic procedures", "context_info")
    ]
    
    for text, expected_type in test_cases:
        chunks = chunker.preprocess_markdown(text, "test.pdf")
        
        found_type = chunks[0].content_type if chunks else "none"
        confidence = chunks[0].confidence_score if chunks else 0.0
        
        print(f"Text: {text}")
        print(f"Expected: {expected_type}")
        print(f"Found: {found_type} (confidence: {confidence:.2f})")
        
        success = (found_type == expected_type)
        print(f"Result: {'PASS' if success else 'FAIL'}\n")

if __name__ == "__main__":
    print("Starting BasicIntelligentChunker Tests\n")
    
    # Run all tests
    chunks = test_chunker_basic()
    test_cpt_code_extraction() 
    test_auth_requirement_detection()
    test_state_detection()
    test_content_classification()
    
    print("Test suite completed!")