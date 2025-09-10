"""UnitedHealthcare Parser Rules and Pattern Definitions.

This module contains specific rules and patterns for parsing UHC prior-authorization
documents, including category-specific parsing logic and validation rules.
"""

import re
from typing import Dict, List, Pattern, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

# Import our models
from models.entities import (
    Rule, RuleType, AuthRequirement,
    CPTCode, ICDCode, State,
    Payer, Category, Service
)


class UHCCategory(str, Enum):
    """Known UHC prior-authorization categories."""
    RADIOLOGY = "radiology"
    CARDIOLOGY = "cardiology"
    ORTHOPEDIC = "orthopedic_surgery"
    NEUROLOGY = "neurology"
    ONCOLOGY = "oncology"
    GASTROENTEROLOGY = "gastroenterology"
    PULMONOLOGY = "pulmonology"
    RHEUMATOLOGY = "rheumatology"
    ENDOCRINOLOGY = "endocrinology"
    DERMATOLOGY = "dermatology"
    OPHTHALMOLOGY = "ophthalmology"
    OTOLARYNGOLOGY = "otolaryngology"
    UROLOGY = "urology"
    GYNECOLOGY = "gynecology"
    PSYCHIATRY = "psychiatry"
    PHYSICAL_THERAPY = "physical_therapy"
    OCCUPATIONAL_THERAPY = "occupational_therapy"
    SPEECH_THERAPY = "speech_therapy"
    HOME_HEALTH = "home_health"
    DME = "durable_medical_equipment"
    PHARMACY = "pharmacy"


@dataclass
class ParsingPattern:
    """A pattern for extracting information from UHC documents."""
    name: str
    pattern: Pattern[str]
    description: str
    extract_groups: List[str]


class UHCParserRules:
    """Collection of parsing rules specific to UnitedHealthcare documents."""
    
    # Compile patterns for better performance
    CPT_PATTERN = re.compile(r'\b(\d{5})\b')
    CPT_RANGE_PATTERN = re.compile(r'\b(\d{5})\s*[-]\s*(\d{5})\b')
    HCPCS_PATTERN = re.compile(r'\b([A-V]\d{4})\b')
    ICD_PATTERN = re.compile(r'\b([A-Z]\d{2}(?:\.\d{1,4})?)\b')
    STATE_PATTERN = re.compile(r'\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC)\b')
    PAGE_PATTERN = re.compile(r'Page\s+(\d+)', re.IGNORECASE)
    
    # Category detection patterns
    CATEGORY_PATTERNS = {
        UHCCategory.RADIOLOGY: [
            re.compile(r'\b(radiology|imaging|mri|ct|pet|scan)\b', re.IGNORECASE),
            re.compile(r'\b(magnetic resonance|computed tomography)\b', re.IGNORECASE)
        ],
        UHCCategory.CARDIOLOGY: [
            re.compile(r'\b(cardiology|cardiac|heart|cardiovascular)\b', re.IGNORECASE),
            re.compile(r'\b(echocardiogram|stress test|catheterization)\b', re.IGNORECASE)
        ],
        UHCCategory.ORTHOPEDIC: [
            re.compile(r'\b(orthopedic|orthopedics|joint|spine|bone)\b', re.IGNORECASE),
            re.compile(r'\b(arthroscopy|replacement|fusion)\b', re.IGNORECASE)
        ]
    }
    
    # Authorization requirement patterns
    AUTH_REQUIRED_PATTERNS = [
        re.compile(r'\b(prior authorization required|requires prior authorization|PA required)\b', re.IGNORECASE),
        re.compile(r'\b(must obtain authorization|authorization needed)\b', re.IGNORECASE)
    ]
    
    AUTH_NOT_REQUIRED_PATTERNS = [
        re.compile(r'\b(no prior authorization|not required|no PA required)\b', re.IGNORECASE),
        re.compile(r'\b(authorization not needed|no authorization required)\b', re.IGNORECASE)
    ]
    
    NOTIFICATION_PATTERNS = [
        re.compile(r'\b(notification only|notify only|notification required)\b', re.IGNORECASE)
    ]
    
    # State exception patterns
    STATE_EXCEPTION_PATTERNS = {
        'excluded': [
            re.compile(r'\b(?:except|excluding|not applicable in|does not apply to)\s+(.+?)\b', re.IGNORECASE),
            re.compile(r'\b(.+?)\s+(?:excluded|not covered)\b', re.IGNORECASE)
        ],
        'included': [
            re.compile(r'\b(?:only in|limited to|applicable only in)\s+(.+?)\b', re.IGNORECASE),
            re.compile(r'\b(.+?)\s+only\b', re.IGNORECASE)
        ]
    }
    
    # Complex narrative indicators
    COMPLEX_NARRATIVE_PATTERNS = [
        re.compile(r'\b(when used for|in combination with|following criteria)\b', re.IGNORECASE),
        re.compile(r'\b(must meet|clinical indications|medical necessity)\b', re.IGNORECASE),
        re.compile(r'\b(diagnosis of|treatment of|management of)\b', re.IGNORECASE),
        re.compile(r'\b(age restrictions|quantity limits|frequency limits)\b', re.IGNORECASE)
    ]
    
    @classmethod
    def detect_category(cls, text: str) -> Optional[UHCCategory]:
        """Detect the category from text using pattern matching."""
        text_lower = text.lower()
        
        for category, patterns in cls.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(text):
                    return category
        
        return None
    
    @classmethod
    def extract_auth_requirement(cls, text: str) -> AuthRequirement:
        """Extract authorization requirement from text."""
        for pattern in cls.AUTH_REQUIRED_PATTERNS:
            if pattern.search(text):
                return AuthRequirement.REQUIRED
        
        for pattern in cls.AUTH_NOT_REQUIRED_PATTERNS:
            if pattern.search(text):
                return AuthRequirement.NOT_REQUIRED
        
        for pattern in cls.NOTIFICATION_PATTERNS:
            if pattern.search(text):
                return AuthRequirement.NOTIFICATION_ONLY
        
        return AuthRequirement.CONDITIONAL  # Default
    
    @classmethod
    def extract_cpt_codes(cls, text: str) -> List[str]:
        """Extract CPT codes from text."""
        codes = []
        
        # Extract regular CPT codes
        codes.extend(cls.CPT_PATTERN.findall(text))
        
        # Extract HCPCS codes
        codes.extend(cls.HCPCS_PATTERN.findall(text))
        
        # Handle CPT ranges
        ranges = cls.CPT_RANGE_PATTERN.findall(text)
        for start, end in ranges:
            codes.append(f"RANGE_{start}_{end}")
        
        return list(set(codes))  # Remove duplicates
    
    @classmethod
    def extract_icd_codes(cls, text: str) -> List[str]:
        """Extract ICD codes from text."""
        return cls.ICD_PATTERN.findall(text)
    
    @classmethod
    def extract_state_exceptions(cls, text: str) -> Tuple[List[str], List[str]]:
        """Extract state exceptions from text.
        
        Returns:
            Tuple of (excluded_states, included_states)
        """
        excluded_states = []
        included_states = []
        
        # Extract excluded states
        for pattern in cls.STATE_EXCEPTION_PATTERNS['excluded']:
            matches = pattern.findall(text)
            for match in matches:
                states = cls.STATE_PATTERN.findall(match)
                excluded_states.extend(states)
        
        # Extract included states
        for pattern in cls.STATE_EXCEPTION_PATTERNS['included']:
            matches = pattern.findall(text)
            for match in matches:
                states = cls.STATE_PATTERN.findall(match)
                included_states.extend(states)
        
        return list(set(excluded_states)), list(set(included_states))
    
    @classmethod
    def is_complex_narrative(cls, text: str) -> bool:
        """Check if text contains complex narrative requiring LLM processing."""
        for pattern in cls.COMPLEX_NARRATIVE_PATTERNS:
            if pattern.search(text):
                return True
        return False
    
    @classmethod
    def extract_page_number(cls, text: str) -> Optional[int]:
        """Extract page number from text."""
        match = cls.PAGE_PATTERN.search(text)
        return int(match.group(1)) if match else None


# Category-specific parsing rules
CATEGORY_SPECIFIC_RULES = {
    UHCCategory.RADIOLOGY: {
        'required_fields': ['cpt_codes', 'auth_requirement'],
        'common_patterns': [
            r'\b(contrast|without contrast|with and without contrast)\b',
            r'\b(bilateral|unilateral)\b',
            r'\b(screening|diagnostic)\b'
        ],
        'exclusions': [
            'emergency situations',
            'inpatient procedures'
        ]
    },
    
    UHCCategory.ORTHOPEDIC: {
        'required_fields': ['cpt_codes', 'auth_requirement', 'icd_codes'],
        'common_patterns': [
            r'\b(arthroscopy|arthroplasty|fusion)\b',
            r'\b(knee|hip|shoulder|spine)\b',
            r'\b(revision|primary)\b'
        ],
        'state_exceptions': ['CA', 'NY']  # Common state exclusions
    },
    
    UHCCategory.CARDIOLOGY: {
        'required_fields': ['cpt_codes', 'auth_requirement'],
        'common_patterns': [
            r'\b(diagnostic|interventional)\b',
            r'\b(catheterization|angioplasty|stent)\b',
            r'\b(left heart|right heart)\b'
        ],
        'age_restrictions': {'min_age': 18}
    }
}


def get_category_rules(category: UHCCategory) -> Dict[str, Any]:
    """Get parsing rules specific to a category."""
    return CATEGORY_SPECIFIC_RULES.get(category, {})


def validate_extracted_rule(rule: Rule) -> List[str]:
    """Validate an extracted rule against UHC-specific requirements.
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Check required fields
    if not rule.cpt_codes and not rule.icd_codes:
        errors.append("Rule must have either CPT or ICD codes")
    
    # Validate CPT codes format
    for code in rule.cpt_codes:
        if code.startswith('RANGE_'):
            continue  # Skip range validation
        if not (len(code) == 5 and code.isdigit()) and not re.match(r'^[A-V]\d{4}$', code):
            errors.append(f"Invalid CPT/HCPCS code format: {code}")
    
    # Validate state codes
    for state in rule.excluded_states + rule.included_states:
        if not re.match(r'^[A-Z]{2}$', state):
            errors.append(f"Invalid state code: {state}")
    
    # Check category-specific rules
    if rule.category:
        try:
            category = UHCCategory(rule.category.lower())
            category_rules = get_category_rules(category)
            
            required_fields = category_rules.get('required_fields', [])
            for field in required_fields:
                if field == 'cpt_codes' and not rule.cpt_codes:
                    errors.append(f"Category {category.value} requires CPT codes")
                elif field == 'icd_codes' and not rule.icd_codes:
                    errors.append(f"Category {category.value} requires ICD codes")
                    
        except ValueError:
            # Unknown category, skip validation
            pass
    
    return errors