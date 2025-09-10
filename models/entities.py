"""Pydantic models for prior-authorization entities."""

from typing import List, Optional, Set, Dict, Any
from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re


class AuthRequirement(str, Enum):
    """Types of authorization requirements."""
    REQUIRED = "required"
    NOT_REQUIRED = "not_required"
    CONDITIONAL = "conditional"
    NOTIFICATION_ONLY = "notification_only"


class RuleType(str, Enum):
    """Types of prior-authorization rules."""
    CPT_BASED = "cpt_based"
    ICD_BASED = "icd_based"
    COMBINATION = "combination"
    NARRATIVE = "narrative"


class Payer(BaseModel):
    """Insurance payer/carrier information."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    name: str = Field(..., min_length=1, description="Payer name (e.g., UnitedHealthcare)")
    payer_id: Optional[str] = Field(None, description="Unique payer identifier")
    effective_date: Optional[date] = Field(None, description="Policy effective date")
    
    # Provenance
    source_file: Optional[str] = Field(None, description="Source PDF file path")
    extraction_timestamp: datetime = Field(default_factory=datetime.now)


class Category(BaseModel):
    """Service category or specialty area."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    name: str = Field(..., min_length=1, description="Category name (e.g., Radiology, Cardiology)")
    parent_category: Optional[str] = Field(None, description="Parent category if hierarchical")
    description: Optional[str] = Field(None, description="Category description")
    
    # Provenance
    source_page: Optional[int] = Field(None, description="Page number in source document")
    source_line: Optional[int] = Field(None, description="Line number on page")


class Service(BaseModel):
    """Medical service or procedure."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    name: str = Field(..., min_length=1, description="Service name")
    description: Optional[str] = Field(None, description="Service description")
    category: Optional[str] = Field(None, description="Service category")
    
    # Provenance
    source_page: Optional[int] = Field(None, description="Page number in source document")
    source_line: Optional[int] = Field(None, description="Line number on page")


class CPTCode(BaseModel):
    """CPT/HCPCS code with validation."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    code: str = Field(..., description="CPT or HCPCS code")
    description: Optional[str] = Field(None, description="Code description")
    is_range: bool = Field(False, description="Whether this represents a code range")
    range_end: Optional[str] = Field(None, description="End of range if is_range=True")
    
    @field_validator('code')
    @classmethod
    def validate_cpt_code(cls, v: str) -> str:
        """Validate CPT/HCPCS code format."""
        v = v.strip().upper()
        
        # CPT codes: 5 digits (00100-99999)
        # HCPCS Level II: Letter + 4 digits (A0000-V9999)
        # Category III CPT: 4 digits + letter (0001T-9999T)
        
        cpt_pattern = r'^\d{5}$'
        hcpcs_pattern = r'^[A-V]\d{4}$'
        category_iii_pattern = r'^\d{4}[A-Z]$'
        
        if not (re.match(cpt_pattern, v) or 
                re.match(hcpcs_pattern, v) or 
                re.match(category_iii_pattern, v)):
            # Allow placeholder for ranges or special cases
            if not v.startswith('RANGE_') and v != 'UNLISTED':
                raise ValueError(f"Invalid CPT/HCPCS code format: {v}")
        
        return v
    
    @field_validator('range_end')
    @classmethod
    def validate_range_end(cls, v: Optional[str], values) -> Optional[str]:
        """Validate range_end format if provided."""
        if v is not None:
            v = v.strip().upper()
            # Apply same validation as code field
            cpt_pattern = r'^\d{5}$'
            hcpcs_pattern = r'^[A-V]\d{4}$'
            category_iii_pattern = r'^\d{4}[A-Z]$'
            
            if not (re.match(cpt_pattern, v) or 
                    re.match(hcpcs_pattern, v) or 
                    re.match(category_iii_pattern, v)):
                raise ValueError(f"Invalid range_end code format: {v}")
        
        return v


class ICDCode(BaseModel):
    """ICD diagnosis code with validation."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    code: str = Field(..., description="ICD-10 code")
    description: Optional[str] = Field(None, description="Diagnosis description")
    version: str = Field("ICD-10", description="ICD version (ICD-10 or ICD-11)")
    
    @field_validator('code')
    @classmethod
    def validate_icd_code(cls, v: str) -> str:
        """Validate ICD-10 code format."""
        v = v.strip().upper()
        
        # ICD-10 format: Letter + 2-7 alphanumeric characters
        # Examples: A00, A00.0, A00.00, M79.3
        icd10_pattern = r'^[A-Z]\d{2}(\.\d{1,4})?$'
        
        if not re.match(icd10_pattern, v):
            # Allow placeholder values
            if not v.startswith('GROUP_') and v != 'ANY':
                raise ValueError(f"Invalid ICD-10 code format: {v}")
        
        return v


class State(BaseModel):
    """US state with validation."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    code: str = Field(..., description="Two-letter state code")
    name: Optional[str] = Field(None, description="Full state name")
    
    @field_validator('code')
    @classmethod
    def validate_state_code(cls, v: str) -> str:
        """Validate US state code."""
        v = v.strip().upper()
        
        # List of valid US state codes
        valid_states = {
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
            'DC', 'PR', 'VI', 'GU', 'AS', 'MP'  # Include territories
        }
        
        if v not in valid_states and v != 'ALL':
            raise ValueError(f"Invalid state code: {v}")
        
        return v


class Plan(BaseModel):
    """Insurance plan information."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    name: str = Field(..., min_length=1, description="Plan name")
    plan_type: Optional[str] = Field(None, description="Plan type (e.g., HMO, PPO, POS)")
    payer: Optional[str] = Field(None, description="Associated payer name")
    
    # Coverage specifics
    excluded_states: List[str] = Field(default_factory=list, description="States where plan doesn't apply")
    included_states: List[str] = Field(default_factory=list, description="States where plan applies")
    
    # Provenance
    source_page: Optional[int] = Field(None, description="Page number in source document")


class Rule(BaseModel):
    """Prior-authorization rule with all associated metadata."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    # Core rule information
    rule_id: Optional[str] = Field(None, description="Unique rule identifier")
    rule_type: RuleType = Field(..., description="Type of rule")
    auth_requirement: AuthRequirement = Field(..., description="Authorization requirement")
    
    # Associated entities
    payer: str = Field(..., description="Payer name")
    category: Optional[str] = Field(None, description="Service category")
    service: Optional[str] = Field(None, description="Service name")
    
    # Codes
    cpt_codes: List[str] = Field(default_factory=list, description="Associated CPT/HCPCS codes")
    icd_codes: List[str] = Field(default_factory=list, description="Required ICD codes")
    
    # Conditions and exceptions
    excluded_states: List[str] = Field(default_factory=list, description="States where rule doesn't apply")
    included_states: List[str] = Field(default_factory=list, description="States where rule applies")
    applicable_plans: List[str] = Field(default_factory=list, description="Specific plans this applies to")
    
    # Additional requirements
    age_restrictions: Optional[Dict[str, Any]] = Field(None, description="Age-based restrictions")
    quantity_limits: Optional[Dict[str, Any]] = Field(None, description="Quantity/frequency limits")
    clinical_criteria: Optional[str] = Field(None, description="Clinical requirements narrative")
    
    # Narrative text (for complex rules requiring LLM processing)
    narrative_text: Optional[str] = Field(None, description="Original narrative text")
    requires_llm_processing: bool = Field(False, description="Flag for complex narrative rules")
    
    # Provenance and metadata
    source_file: str = Field(..., description="Source PDF file")
    source_page: int = Field(..., description="Page number in source")
    source_line: Optional[int] = Field(None, description="Line number on page")
    extraction_timestamp: datetime = Field(default_factory=datetime.now)
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Extraction confidence")
    
    # Additional metadata
    effective_date: Optional[date] = Field(None, description="Rule effective date")
    expiration_date: Optional[date] = Field(None, description="Rule expiration date")
    last_updated: Optional[date] = Field(None, description="Last update date")
    
    def __str__(self) -> str:
        """String representation for debugging."""
        codes = ', '.join(self.cpt_codes) if self.cpt_codes else 'No codes'
        return f"Rule({self.auth_requirement.value}: {self.service or self.category} - {codes})"
    
    def to_hyperedge(self) -> Dict[str, Any]:
        """Convert rule to hyperedge representation for graph database."""
        return {
            'id': self.rule_id or f"{self.payer}_{self.category}_{'-'.join(self.cpt_codes[:3])}",
            'type': 'authorization_rule',
            'auth_requirement': self.auth_requirement.value,
            'nodes': {
                'payer': self.payer,
                'category': self.category,
                'service': self.service,
                'cpt_codes': self.cpt_codes,
                'icd_codes': self.icd_codes,
                'states': self.excluded_states + self.included_states,
                'plans': self.applicable_plans
            },
            'properties': {
                'clinical_criteria': self.clinical_criteria,
                'age_restrictions': self.age_restrictions,
                'quantity_limits': self.quantity_limits,
                'effective_date': self.effective_date.isoformat() if self.effective_date else None,
                'source': {
                    'file': self.source_file,
                    'page': self.source_page,
                    'line': self.source_line
                }
            }
        }