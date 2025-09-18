"""Enhanced UHC rule parser with advanced pattern recognition for real-world complexity."""

import re
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Import models
try:
    from src.models import Rule, RuleType, AuthRequirement
    from src.models_enhanced import (
        EnhancedRule, PlaceOfService, DiagnosisException, 
        AgeRestriction, ProviderRestriction, ConditionalLogic
    )
except ImportError:
    from models import Rule, RuleType, AuthRequirement
    from models_enhanced import (
        EnhancedRule, PlaceOfService, DiagnosisException,
        AgeRestriction, ProviderRestriction, ConditionalLogic
    )


class AdvancedPatternExtractor:
    """Advanced pattern extraction for complex authorization logic"""
    
    def __init__(self):
        # Core code patterns
        self.cpt_pattern = r'\b(\d{5})\b'
        self.cpt_range_pattern = r'\b(\d{5})\s*[-–]\s*(\d{5})\b'
        self.hcpcs_pattern = r'\b([A-V]\d{4})\b'
        self.icd_pattern = r'\b([A-Z]\d{2}(?:\.\d{1,4})?)\b'
        self.state_pattern = r'\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC)\b'
        
        # Place of Service patterns
        self.pos_patterns = {
            'office': r'(?i)(?:office|physician[\'s]?\s*office|outpatient\s*office)',
            'outpatient_hospital': r'(?i)(?:outpatient\s*hospital|hospital\s*outpatient|ambulatory\s*surgical)',
            'inpatient_hospital': r'(?i)(?:inpatient\s*hospital|hospital\s*inpatient)',
            'ambulatory_surgical': r'(?i)(?:ambulatory\s*surgical\s*center|ASC|surgery\s*center)',
            'home': r'(?i)(?:home|patient[\'s]?\s*home)',
            'facility': r'(?i)(?:facility|medical\s*facility)'
        }
        
        # Authorization requirement patterns
        self.auth_patterns = {
            'required': [
                r'(?i)prior\s*authorization\s*(?:is\s*)?required',
                r'(?i)requires?\s*prior\s*authorization',
                r'(?i)PA\s*required',
                r'(?i)authorization\s*necessary'
            ],
            'not_required': [
                r'(?i)(?:no|not)\s*(?:prior\s*)?authorization\s*(?:is\s*)?(?:required|necessary)',
                r'(?i)authorization\s*not\s*required',
                r'(?i)no\s*PA\s*required'
            ],
            'notification_only': [
                r'(?i)notification\s*only',
                r'(?i)notify\s*only',
                r'(?i)advance\s*notification'
            ]
        }
        
        # Place of Service specific patterns
        self.pos_auth_patterns = {
            'office_not_required': r'(?i)(?:not\s*required|no\s*authorization)\s*(?:if|when)\s*performed\s*in\s*(?:an?\s*)?(?:office|physician[\'s]?\s*office)',
            'outpatient_required': r'(?i)(?:required|authorization)\s*(?:only\s*)?(?:when|if)\s*(?:requesting\s*service\s*in|performed\s*in)\s*(?:an?\s*)?outpatient\s*hospital',
            'facility_review': r'(?i)site\s*of\s*service\s*(?:will\s*be\s*)?review(?:ed)?'
        }
        
        # Diagnosis exception patterns  
        self.diagnosis_exception_patterns = [
            r'(?i)(?:not\s*required|no\s*authorization)\s*for\s*(?:the\s*)?following\s*diagnosis\s*codes?',
            r'(?i)diagnosis\s*codes?\s*(?:that\s*)?(?:exempt|do\s*not\s*require)',
            r'(?i)(?:exempt|exception)\s*diagnosis\s*codes?'
        ]
        
        # Age-based patterns
        self.age_patterns = [
            r'(?i)(?:patients?\s*)?ages?\s*(\d+)\s*(?:and\s*)?(?:older|above|over|\+)',
            r'(?i)(?:patients?\s*)?(?:under|below)\s*(?:age\s*)?(\d+)',
            r'(?i)(?:patients?\s*)?ages?\s*(\d+)\s*(?:to|-)\s*(\d+)',
            r'(?i)pediatric\s*(?:patients?)?',
            r'(?i)adult\s*(?:patients?)?'
        ]
        
        # Geographic exception patterns
        self.geographic_patterns = [
            r'(?i)(?:except|excluding)\s*in\s*([A-Z]{2}(?:,?\s*[A-Z]{2})*)',
            r'(?i)(?:all\s*states\s*)?except\s*(?:in\s*)?([^.]+)',
            r'(?i)(?:limited\s*to|only\s*in)\s*([A-Z]{2}(?:,?\s*[A-Z]{2})*)',
            r'(?i)except\s*in\s*([^.]+)'
        ]
    
    def extract_place_of_service_rules(self, text: str) -> List[PlaceOfService]:
        """Extract place of service specific authorization rules"""
        pos_rules = []
        
        # Check for office vs outpatient hospital patterns
        if re.search(self.pos_auth_patterns['office_not_required'], text):
            pos_rules.append(PlaceOfService(
                pos_code="11",
                description="Office",
                requires_auth=False,
                preferred_setting=True,
                review_type="EXEMPT"
            ))
        
        if re.search(self.pos_auth_patterns['outpatient_required'], text):
            pos_rules.append(PlaceOfService(
                pos_code="22", 
                description="Outpatient Hospital",
                requires_auth=True,
                preferred_setting=False,
                review_type="PRIOR_AUTH"
            ))
        
        if re.search(self.pos_auth_patterns['facility_review'], text):
            pos_rules.append(PlaceOfService(
                pos_code="*",
                description="Site of service review required",
                requires_auth=True,
                preferred_setting=False,
                review_type="SITE_OF_SERVICE"
            ))
        
        return pos_rules
    
    def extract_diagnosis_exceptions(self, text: str, context_lines: List[str] = None) -> List[DiagnosisException]:
        """Extract diagnosis code exceptions that modify authorization requirements"""
        exceptions = []
        
        for pattern in self.diagnosis_exception_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                # Extract ICD codes following the exception pattern
                start_pos = match.end()
                remaining_text = text[start_pos:start_pos+500]  # Look ahead 500 chars
                
                icd_codes = re.findall(self.icd_pattern, remaining_text)
                if icd_codes:
                    exceptions.append(DiagnosisException(
                        icd_codes=icd_codes,
                        exception_type="EXEMPT",
                        description=f"Diagnosis exception: {match.group(0)}"
                    ))
        
        return exceptions
    
    def extract_age_restrictions(self, text: str) -> List[AgeRestriction]:
        """Extract age-based authorization rules"""
        restrictions = []
        
        # Age 18 and older pattern
        age_older_matches = re.finditer(self.age_patterns[0], text)
        for match in age_older_matches:
            min_age = int(match.group(1))
            auth_req = AuthRequirement.REQUIRED if 'required' in text[match.start()-50:match.end()+50].lower() else AuthRequirement.CONDITIONAL
            
            restrictions.append(AgeRestriction(
                min_age=min_age,
                max_age=None,
                age_units="YEARS",
                special_population="ADULT" if min_age >= 18 else "PEDIATRIC",
                auth_requirement=auth_req
            ))
        
        # Under age X pattern
        age_under_matches = re.finditer(self.age_patterns[1], text)
        for match in age_under_matches:
            max_age = int(match.group(1)) - 1
            
            restrictions.append(AgeRestriction(
                min_age=None,
                max_age=max_age,
                age_units="YEARS", 
                special_population="PEDIATRIC",
                auth_requirement=AuthRequirement.CONDITIONAL  # Often refers to different section
            ))
        
        return restrictions
    
    def extract_geographic_exceptions(self, text: str) -> Tuple[List[str], List[str]]:
        """Extract geographic exceptions (excluded_states, included_states)"""
        excluded_states = []
        included_states = []
        
        # State name to abbreviation mapping
        state_mapping = {
            'alaska': 'AK', 'massachusetts': 'MA', 'puerto rico': 'PR', 
            'rhode island': 'RI', 'texas': 'TX', 'utah': 'UT', 
            'virgin islands': 'VI', 'wisconsin': 'WI'
        }
        
        # Look for exception patterns
        for pattern in self.geographic_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                state_text = match.group(1).lower()
                
                # Extract 2-letter state codes
                state_codes = re.findall(r'\b([A-Z]{2})\b', match.group(1))
                excluded_states.extend(state_codes)
                
                # Extract state names and convert to abbreviations
                for state_name, abbreviation in state_mapping.items():
                    if state_name in state_text:
                        excluded_states.append(abbreviation)
        
        return list(set(excluded_states)), list(set(included_states))
    
    def extract_conditional_logic(self, text: str) -> List[ConditionalLogic]:
        """Extract complex conditional authorization logic"""
        conditions = []
        
        # Pattern: "required for all states EXCEPT..."
        all_states_except_patterns = [
            r'(?i)(?:required\s*for\s*)?all\s*states[^.]*except\s*(?:in\s*)?([^.]+)',
            r'(?i)prior\s*authorization\s*(?:is\s*)?required\s*(?:for\s*)?(?:all\s*states\s*)?except\s*(?:in\s*)?([^.]+)',
            r'(?i)all\s*states[^.]*except\s*in\s*([^.]+)'
        ]
        
        for pattern in all_states_except_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                exception_text = match.group(1)
                
                # Extract both state codes and convert state names
                excluded_states = []
                state_codes = re.findall(r'\b([A-Z]{2})\b', exception_text)
                excluded_states.extend(state_codes)
                
                # State name mapping
                state_mapping = {
                    'alaska': 'AK', 'massachusetts': 'MA', 'puerto rico': 'PR', 
                    'rhode island': 'RI', 'texas': 'TX', 'utah': 'UT', 
                    'virgin islands': 'VI', 'wisconsin': 'WI'
                }
                
                exception_lower = exception_text.lower()
                for state_name, abbreviation in state_mapping.items():
                    if state_name in exception_lower:
                        excluded_states.append(abbreviation)
                
                if excluded_states:
                    conditions.append(ConditionalLogic(
                        condition_type="IF_THEN",
                        conditions=[
                            {"type": "state_not_in", "values": list(set(excluded_states))},
                            {"type": "auth_required", "value": True}
                        ],
                        result_auth_requirement=AuthRequirement.REQUIRED,
                        priority=1
                    ))
        
        return conditions


def parse_markdown_to_enhanced_rules(markdown_text: str, source_file: str = "unknown.pdf") -> List[EnhancedRule]:
    """Parse markdown text into enhanced rules with advanced pattern recognition.
    
    This function enhances the original parser with:
    - Place of service detection
    - Diagnosis exception extraction  
    - Age-based rule parsing
    - Complex conditional logic
    - Geographic exception handling
    """
    
    extractor = AdvancedPatternExtractor()
    enhanced_rules = []
    
    # Split text into lines for processing
    lines = markdown_text.split('\n')
    
    # Track context
    current_category = None
    current_service = None
    current_page = 1
    
    # Process text in larger sections to capture multi-line patterns
    text_sections = []
    current_section = []
    
    for i, line in enumerate(lines):
        current_section.append(line)
        
        # Create sections at logical breaks, but with larger chunks
        if (i == len(lines) - 1 or 
            (not line.strip() and len(current_section) > 10) or
            (line.strip().isupper() and len(line.strip()) > 20)):
            
            if current_section:
                section_text = '\n'.join(current_section)
                if section_text.strip():
                    text_sections.append({
                        'text': section_text,
                        'start_line': i - len(current_section) + 1,
                        'end_line': i
                    })
                current_section = []
    
    # Also process the entire text as one section for complex patterns
    text_sections.append({
        'text': markdown_text,
        'start_line': 1,
        'end_line': len(lines)
    })
    
    # Process each section for rules
    for section in text_sections:
        section_text = section['text']
        
        # Extract codes using original patterns
        cpt_matches = re.findall(extractor.cpt_pattern, section_text)
        hcpcs_matches = re.findall(extractor.hcpcs_pattern, section_text)
        all_codes = list(cpt_matches) + list(hcpcs_matches)
        
        # If we found codes, this might be a rule section
        if all_codes:
            # Determine base authorization requirement
            auth_requirement = AuthRequirement.CONDITIONAL  # Default
            section_lower = section_text.lower()
            
            # Check for authorization patterns
            for req_type, patterns in extractor.auth_patterns.items():
                if any(re.search(pattern, section_text) for pattern in patterns):
                    if req_type == 'required':
                        auth_requirement = AuthRequirement.REQUIRED
                    elif req_type == 'not_required':
                        auth_requirement = AuthRequirement.NOT_REQUIRED
                    elif req_type == 'notification_only':
                        auth_requirement = AuthRequirement.NOTIFICATION_ONLY
                    break
            
            # Extract enhanced components
            pos_rules = extractor.extract_place_of_service_rules(section_text)
            diagnosis_exceptions = extractor.extract_diagnosis_exceptions(section_text)
            age_restrictions = extractor.extract_age_restrictions(section_text)
            excluded_states, included_states = extractor.extract_geographic_exceptions(section_text)
            conditional_logic = extractor.extract_conditional_logic(section_text)
            
            # Determine service name from section content
            service_name = None
            lines_in_section = section_text.split('\n')
            for line in lines_in_section:
                if line.strip() and not re.search(r'\d{5}', line):
                    # Likely a service name line
                    service_name = line.strip()
                    break
            
            # Create enhanced rule
            enhanced_rule = EnhancedRule(
                rule_type=RuleType.CPT_BASED,
                auth_requirement=auth_requirement,
                payer="UnitedHealthcare",
                category=current_category,
                service=service_name or "Extracted Rule",
                cpt_codes=all_codes,
                
                # Enhanced features
                place_of_service_restrictions=pos_rules,
                diagnosis_exceptions=diagnosis_exceptions,
                age_restrictions=age_restrictions,
                conditional_logic=conditional_logic,
                
                # Geographic
                excluded_states=excluded_states,
                included_states=included_states,
                
                # Provenance
                source_file=source_file,
                source_page=current_page,
                source_line=section['start_line'],
                extraction_timestamp=datetime.now(),
                confidence_score=0.85  # Higher confidence for enhanced extraction
            )
            
            enhanced_rules.append(enhanced_rule)
    
    print(f"Enhanced parser extracted {len(enhanced_rules)} rules with advanced features")
    
    # Log enhanced features found
    pos_count = sum(1 for rule in enhanced_rules if rule.place_of_service_restrictions)
    dx_count = sum(1 for rule in enhanced_rules if rule.diagnosis_exceptions)
    age_count = sum(1 for rule in enhanced_rules if rule.age_restrictions)
    geo_count = sum(1 for rule in enhanced_rules if rule.excluded_states or rule.included_states)
    cond_count = sum(1 for rule in enhanced_rules if rule.conditional_logic)
    
    print(f"Enhanced features found: {pos_count} POS rules, {dx_count} diagnosis exceptions, "
          f"{age_count} age restrictions, {geo_count} geographic rules, {cond_count} conditional logic")
    
    return enhanced_rules


# Backward compatibility function
def parse_markdown_to_rules(markdown_text: str, source_file: str = "unknown.pdf") -> List[Rule]:
    """Backward compatible function that returns basic Rule objects"""
    enhanced_rules = parse_markdown_to_enhanced_rules(markdown_text, source_file)
    
    # Convert to basic rules for compatibility
    basic_rules = []
    for enhanced_rule in enhanced_rules:
        # Create basic rule with core fields
        basic_rule = Rule(
            rule_type=enhanced_rule.rule_type,
            auth_requirement=enhanced_rule.auth_requirement,
            payer=enhanced_rule.payer,
            category=enhanced_rule.category,
            service=enhanced_rule.service,
            cpt_codes=enhanced_rule.cpt_codes,
            icd_codes=enhanced_rule.icd_codes,
            excluded_states=enhanced_rule.excluded_states,
            included_states=enhanced_rule.included_states,
            source_file=enhanced_rule.source_file,
            source_page=enhanced_rule.source_page,
            source_line=enhanced_rule.source_line,
            extraction_timestamp=enhanced_rule.extraction_timestamp,
            confidence_score=enhanced_rule.confidence_score
        )
        basic_rules.append(basic_rule)
    
    return basic_rules