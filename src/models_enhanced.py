"""Enhanced Pydantic models for comprehensive prior-authorization system."""

from typing import List, Optional, Set, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re
try:
    from .models import Rule, AuthRequirement, RuleType  # Import existing models
except ImportError:
    from models import Rule, AuthRequirement, RuleType  # Fallback for direct imports


class PlaceOfService(BaseModel):
    """Place of service codes and restrictions."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    pos_code: str = Field(..., description="POS code (11=Office, 22=Outpatient Hospital, etc.)")
    description: str = Field(..., description="POS description")
    requires_auth: bool = Field(False, description="Whether this POS requires auth")
    preferred_setting: bool = Field(False, description="Whether this is the preferred setting")
    review_type: Optional[str] = Field(None, description="PRIOR_AUTH, SITE_OF_SERVICE, NOTIFICATION")


class DiagnosisException(BaseModel):
    """ICD codes that modify authorization requirements."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    icd_codes: List[str] = Field(..., description="ICD codes that trigger exception")
    exception_type: str = Field(..., description="EXEMPT, REQUIRED, NOTIFICATION_ONLY, CONDITIONAL")
    applies_to_cpt_codes: List[str] = Field(default_factory=list, description="Specific CPT codes this applies to")
    description: Optional[str] = Field(None, description="Human-readable exception description")


class ProviderRestriction(BaseModel):
    """Provider specialty or network restrictions."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    provider_specialties: List[str] = Field(default_factory=list, description="Required provider specialties")
    network_status: Optional[str] = Field(None, description="IN_NETWORK, OUT_OF_NETWORK, EITHER")
    certification_required: List[str] = Field(default_factory=list, description="Required certifications")
    participating_only: bool = Field(False, description="Must be participating provider")


class ConditionalLogic(BaseModel):
    """Complex conditional authorization logic."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    condition_type: str = Field(..., description="AND, OR, NOT, IF_THEN")
    conditions: List[Dict[str, Any]] = Field(..., description="List of condition dictionaries")
    result_auth_requirement: AuthRequirement = Field(..., description="Auth requirement if conditions met")
    priority: int = Field(1, description="Priority order for evaluation")


class AgeRestriction(BaseModel):
    """Age-based restrictions and requirements."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    min_age: Optional[int] = Field(None, ge=0, description="Minimum age")
    max_age: Optional[int] = Field(None, ge=0, description="Maximum age")
    age_units: str = Field("YEARS", description="YEARS, MONTHS, DAYS")
    special_population: Optional[str] = Field(None, description="PEDIATRIC, ADULT, GERIATRIC")
    auth_requirement: AuthRequirement = Field(..., description="Auth requirement for this age group")


class TimeRestriction(BaseModel):
    """Time-based restrictions and limits."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    frequency_limit: Optional[int] = Field(None, description="Max occurrences per time period")
    time_period_days: Optional[int] = Field(None, description="Time period in days")
    requires_interval: Optional[int] = Field(None, description="Required interval between procedures (days)")
    authorization_duration_days: Optional[int] = Field(None, description="How long auth is valid")


class EnhancedRule(Rule):
    """Enhanced prior-authorization rule extending the base Rule model."""
    
    # NEW: Enhanced features (all optional for backward compatibility)
    place_of_service_restrictions: List[PlaceOfService] = Field(
        default_factory=list, 
        description="Place of service specific requirements"
    )
    
    diagnosis_exceptions: List[DiagnosisException] = Field(
        default_factory=list,
        description="ICD codes that modify auth requirements"
    )
    
    provider_restrictions: Optional[ProviderRestriction] = Field(
        None,
        description="Provider specialty/network requirements"
    )
    
    age_restrictions: List[AgeRestriction] = Field(
        default_factory=list,
        description="Age-specific authorization requirements"
    )
    
    time_restrictions: Optional[TimeRestriction] = Field(
        None,
        description="Frequency and timing restrictions"
    )
    
    conditional_logic: List[ConditionalLogic] = Field(
        default_factory=list,
        description="Complex conditional authorization rules"
    )
    
    @classmethod
    def from_basic_rule(cls, basic_rule: Rule) -> 'EnhancedRule':
        """Convert a basic Rule to an EnhancedRule."""
        rule_data = basic_rule.model_dump()
        
        # Remove fields that conflict with enhanced model or set proper defaults
        rule_data.pop('age_restrictions', None)  # Remove legacy field
        rule_data.pop('quantity_limits', None)   # Remove legacy field
        
        return cls(**rule_data)
    
    def evaluate_authorization(self, 
                             patient_age: Optional[int] = None,
                             diagnosis_codes: List[str] = None,
                             place_of_service: Optional[str] = None,
                             provider_specialty: Optional[str] = None,
                             patient_state: Optional[str] = None,
                             plan_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Evaluate authorization requirement based on patient/provider context.
        
        Returns:
            Dict with 'auth_required', 'reason', 'confidence' keys
        """
        diagnosis_codes = diagnosis_codes or []
        
        # Check geographic exclusions
        if patient_state and patient_state in self.excluded_states:
            return {
                'auth_required': False,
                'reason': f'Geographic exclusion: {patient_state}',
                'confidence': 1.0
            }
        
        # Check diagnosis exceptions
        for dx_exception in self.diagnosis_exceptions:
            if any(dx in diagnosis_codes for dx in dx_exception.icd_codes):
                if dx_exception.exception_type == 'EXEMPT':
                    return {
                        'auth_required': False,
                        'reason': f'Diagnosis exception: {dx_exception.icd_codes}',
                        'confidence': 0.9
                    }
        
        # Check place of service restrictions
        if place_of_service:
            for pos_restriction in self.place_of_service_restrictions:
                if pos_restriction.pos_code == place_of_service:
                    return {
                        'auth_required': pos_restriction.requires_auth,
                        'reason': f'Place of service rule: {pos_restriction.description}',
                        'confidence': 0.9
                    }
        
        # Check age restrictions
        if patient_age is not None:
            for age_restriction in self.age_restrictions:
                if (age_restriction.min_age is None or patient_age >= age_restriction.min_age) and \
                   (age_restriction.max_age is None or patient_age <= age_restriction.max_age):
                    return {
                        'auth_required': age_restriction.auth_requirement == AuthRequirement.REQUIRED,
                        'reason': f'Age-based rule: {age_restriction.min_age}-{age_restriction.max_age}',
                        'confidence': 0.8
                    }
        
        # Default to base rule
        return {
            'auth_required': self.auth_requirement == AuthRequirement.REQUIRED,
            'reason': 'Base rule',
            'confidence': self.confidence_score or 0.7
        }


class RuleCollection(BaseModel):
    """Collection of related rules with shared context."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    collection_id: str = Field(..., description="Unique collection identifier")
    name: str = Field(..., description="Collection name (e.g., 'UHC Cardiovascular Rules')")
    payer: str = Field(..., description="Associated payer")
    category: Optional[str] = Field(None, description="Service category")
    
    rules: List[Union[Rule, EnhancedRule]] = Field(..., description="Rules in this collection")
    
    # Collection-level metadata
    effective_date: Optional[date] = Field(None, description="When collection becomes effective")
    source_document: str = Field(..., description="Source document filename")
    version: str = Field("1.0", description="Collection version")
    
    def find_applicable_rules(self, cpt_code: str) -> List[Union[Rule, EnhancedRule]]:
        """Find all rules that apply to a given CPT code."""
        return [rule for rule in self.rules if cpt_code in rule.cpt_codes]
    
    def evaluate_authorization_for_cpt(self, 
                                     cpt_code: str,
                                     **evaluation_context) -> Dict[str, Any]:
        """Evaluate authorization for a specific CPT code with context."""
        applicable_rules = self.find_applicable_rules(cpt_code)
        
        if not applicable_rules:
            return {
                'auth_required': False,
                'reason': 'No applicable rules found',
                'confidence': 0.5
            }
        
        # For enhanced rules, use evaluation logic
        results = []
        for rule in applicable_rules:
            if isinstance(rule, EnhancedRule):
                results.append(rule.evaluate_authorization(**evaluation_context))
            else:
                # Basic rule - use simple logic
                results.append({
                    'auth_required': rule.auth_requirement == AuthRequirement.REQUIRED,
                    'reason': 'Basic rule match',
                    'confidence': rule.confidence_score or 0.7
                })
        
        # If any rule requires auth, auth is required
        if any(result['auth_required'] for result in results):
            required_results = [r for r in results if r['auth_required']]
            best_result = max(required_results, key=lambda x: x['confidence'])
            return best_result
        
        # Otherwise, use the highest confidence result
        return max(results, key=lambda x: x['confidence'])