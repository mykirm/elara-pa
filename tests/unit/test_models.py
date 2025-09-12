#!/usr/bin/env python3
"""Unit tests for Pydantic models."""

import sys
from pathlib import Path
import pytest
from datetime import datetime
from pydantic import ValidationError

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import directly from models file to avoid src/__init__ imports
import importlib.util
spec = importlib.util.spec_from_file_location("models", 
    str(Path(__file__).parent.parent.parent / "src" / "models.py"))
models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models)

Rule = models.Rule
RuleType = models.RuleType
AuthRequirement = models.AuthRequirement
CPTCode = models.CPTCode
ICDCode = models.ICDCode
State = models.State
Payer = models.Payer
Category = models.Category
Service = models.Service


class TestCPTCode:
    """Test CPTCode model validation."""
    
    def test_valid_cpt_code(self):
        """Test valid 5-digit CPT code."""
        cpt = CPTCode(code="99213", description="Office visit")
        assert cpt.code == "99213"
        assert cpt.description == "Office visit"
    
    def test_valid_hcpcs_code(self):
        """Test valid HCPCS code (letter + 4 digits)."""
        hcpcs = CPTCode(code="J3490", description="Unclassified drugs")
        assert hcpcs.code == "J3490"
    
    def test_valid_category_iii_code(self):
        """Test valid Category III CPT code."""
        cat3 = CPTCode(code="0001T", description="Category III code")
        assert cat3.code == "0001T"
    
    def test_invalid_cpt_code_letters(self):
        """Test that non-numeric CPT code raises error."""
        with pytest.raises(ValidationError) as exc_info:
            CPTCode(code="ABCDE", description="Invalid")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "Invalid CPT/HCPCS code format" in errors[0]['msg']
    
    def test_invalid_cpt_code_wrong_length(self):
        """Test that wrong length CPT code raises error."""
        with pytest.raises(ValidationError) as exc_info:
            CPTCode(code="1234", description="Too short")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "Invalid CPT/HCPCS code format" in errors[0]['msg']
    
    def test_invalid_hcpcs_code_format(self):
        """Test invalid HCPCS format."""
        with pytest.raises(ValidationError) as exc_info:
            CPTCode(code="ZZ999", description="Invalid HCPCS")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "Invalid CPT/HCPCS code format" in errors[0]['msg']
    
    def test_empty_code(self):
        """Test that empty code raises error."""
        with pytest.raises(ValidationError) as exc_info:
            CPTCode(code="", description="Empty code")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1


class TestICDCode:
    """Test ICDCode model validation."""
    
    def test_valid_icd10_code_simple(self):
        """Test valid simple ICD-10 code."""
        icd = ICDCode(code="M25", description="Joint disorder")
        assert icd.code == "M25"
        assert icd.version == "ICD-10"
    
    def test_valid_icd10_code_with_decimal(self):
        """Test valid ICD-10 code with decimal."""
        icd = ICDCode(code="M25.511", description="Pain in right shoulder")
        assert icd.code == "M25.511"
    
    def test_valid_icd10_code_full_format(self):
        """Test valid full format ICD-10 code."""
        icd = ICDCode(code="M25.5119", description="Pain in unspecified shoulder")
        assert icd.code == "M25.5119"
    
    def test_invalid_icd_code_format(self):
        """Test invalid ICD code format."""
        with pytest.raises(ValidationError) as exc_info:
            ICDCode(code="123.45", description="Invalid format")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "Invalid ICD-10 code format" in errors[0]['msg']
    
    def test_invalid_icd_code_too_many_decimals(self):
        """Test ICD code with too many decimal places."""
        with pytest.raises(ValidationError) as exc_info:
            ICDCode(code="M25.12345", description="Too many decimals")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "Invalid ICD-10 code format" in errors[0]['msg']
    
    def test_icd_code_lowercase_converted(self):
        """Test that lowercase ICD codes are converted to uppercase."""
        icd = ICDCode(code="m25.511", description="Pain in right shoulder")
        assert icd.code == "M25.511"  # Should be uppercase


class TestState:
    """Test State model validation."""
    
    def test_valid_state_code(self):
        """Test valid US state code."""
        state = State(code="CA", name="California")
        assert state.code == "CA"
        assert state.name == "California"
    
    def test_valid_state_dc(self):
        """Test DC is accepted as valid."""
        state = State(code="DC", name="District of Columbia")
        assert state.code == "DC"
    
    def test_invalid_state_code(self):
        """Test invalid state code."""
        with pytest.raises(ValidationError) as exc_info:
            State(code="ZZ", name="Invalid State")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "Invalid US state code" in errors[0]['msg']
    
    def test_lowercase_state_code_converted(self):
        """Test lowercase state codes are converted to uppercase."""
        state = State(code="ca", name="California")
        assert state.code == "CA"


class TestRule:
    """Test Rule model and its methods."""
    
    def test_create_basic_rule(self):
        """Test creating a basic rule."""
        rule = Rule(
            rule_type=RuleType.CPT_BASED,
            auth_requirement=AuthRequirement.REQUIRED,
            payer="UnitedHealthcare",
            cpt_codes=["99213", "99214"]
        )
        assert rule.rule_type == RuleType.CPT_BASED
        assert rule.auth_requirement == AuthRequirement.REQUIRED
        assert len(rule.cpt_codes) == 2
    
    def test_rule_with_all_fields(self):
        """Test rule with all optional fields populated."""
        rule = Rule(
            rule_type=RuleType.COMBINATION,
            auth_requirement=AuthRequirement.CONDITIONAL,
            payer="Aetna",
            category="Cardiology",
            service="Echocardiogram",
            cpt_codes=["93306", "93307"],
            icd_codes=["I21.9", "I25.10"],
            excluded_states=["TX", "FL"],
            included_states=["CA", "NY"],
            age_min=18,
            age_max=65,
            quantity_limit=2,
            time_period_days=365,
            narrative_text="Prior auth required for echo",
            requires_llm_processing=False,
            source_file="aetna_2025.pdf",
            source_page=42,
            source_line=15,
            confidence_score=0.95
        )
        assert rule.category == "Cardiology"
        assert rule.age_min == 18
        assert rule.age_max == 65
        assert len(rule.icd_codes) == 2
        assert len(rule.excluded_states) == 2
        assert rule.confidence_score == 0.95
    
    def test_rule_hyperedge_generation(self):
        """Test hyperedge generation from rule."""
        rule = Rule(
            rule_type=RuleType.CPT_BASED,
            auth_requirement=AuthRequirement.REQUIRED,
            payer="UnitedHealthcare",
            category="Orthopedics",
            cpt_codes=["29826", "29827"],
            excluded_states=["TX"]
        )
        
        hyperedge = rule.to_hyperedge()
        
        assert hyperedge["edge_type"] == "AUTHORIZATION_RULE"
        assert "CPT:29826" in hyperedge["nodes"]
        assert "CPT:29827" in hyperedge["nodes"]
        assert "PAYER:UnitedHealthcare" in hyperedge["nodes"]
        assert "STATE_EXCLUDED:TX" in hyperedge["nodes"]
        assert "CATEGORY:Orthopedics" in hyperedge["nodes"]
        assert hyperedge["properties"]["auth_requirement"] == "REQUIRED"
    
    def test_rule_invalid_confidence_score(self):
        """Test that confidence score must be between 0 and 1."""
        with pytest.raises(ValidationError) as exc_info:
            Rule(
                rule_type=RuleType.CPT_BASED,
                auth_requirement=AuthRequirement.REQUIRED,
                payer="Test",
                confidence_score=1.5  # Invalid: > 1.0
            )
        
        errors = exc_info.value.errors()
        assert any("less than or equal to 1" in str(e) for e in errors)
    
    def test_rule_negative_age(self):
        """Test that negative age values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Rule(
                rule_type=RuleType.CPT_BASED,
                auth_requirement=AuthRequirement.REQUIRED,
                payer="Test",
                age_min=-1  # Invalid: negative
            )
        
        errors = exc_info.value.errors()
        assert any("greater than or equal to 0" in str(e) for e in errors)
    
    def test_rule_age_validation(self):
        """Test age_min must be <= age_max."""
        with pytest.raises(ValidationError) as exc_info:
            Rule(
                rule_type=RuleType.CPT_BASED,
                auth_requirement=AuthRequirement.REQUIRED,
                payer="Test",
                age_min=65,
                age_max=18  # Invalid: max < min
            )
        
        errors = exc_info.value.errors()
        assert any("age_min must be less than or equal to age_max" in str(e) for e in errors)
    
    def test_rule_default_values(self):
        """Test that default values are set correctly."""
        rule = Rule(
            rule_type=RuleType.CPT_BASED,
            auth_requirement=AuthRequirement.REQUIRED,
            payer="Test"
        )
        
        assert rule.cpt_codes == []
        assert rule.icd_codes == []
        assert rule.excluded_states == []
        assert rule.included_states == []
        assert rule.requires_llm_processing is False
        assert rule.created_at is not None
        assert rule.updated_at is not None


class TestEnums:
    """Test enum values."""
    
    def test_rule_type_values(self):
        """Test RuleType enum values."""
        assert RuleType.CPT_BASED.value == "CPT_BASED"
        assert RuleType.DIAGNOSIS_BASED.value == "DIAGNOSIS_BASED"
        assert RuleType.COMBINATION.value == "COMBINATION"
        assert RuleType.SERVICE_BASED.value == "SERVICE_BASED"
    
    def test_auth_requirement_values(self):
        """Test AuthRequirement enum values."""
        assert AuthRequirement.REQUIRED.value == "REQUIRED"
        assert AuthRequirement.NOT_REQUIRED.value == "NOT_REQUIRED"
        assert AuthRequirement.CONDITIONAL.value == "CONDITIONAL"
        assert AuthRequirement.NOTIFICATION_ONLY.value == "NOTIFICATION_ONLY"


class TestPayer:
    """Test Payer model."""
    
    def test_create_payer(self):
        """Test creating a payer."""
        payer = Payer(
            name="UnitedHealthcare",
            code="UHC",
            states_covered=["CA", "TX", "NY"]
        )
        assert payer.name == "UnitedHealthcare"
        assert payer.code == "UHC"
        assert len(payer.states_covered) == 3


class TestCategory:
    """Test Category model."""
    
    def test_create_category(self):
        """Test creating a category."""
        category = Category(
            name="Cardiology",
            code="CARD",
            parent_category="Medical Specialties"
        )
        assert category.name == "Cardiology"
        assert category.code == "CARD"
        assert category.parent_category == "Medical Specialties"


class TestService:
    """Test Service model."""
    
    def test_create_service(self):
        """Test creating a service."""
        service = Service(
            name="MRI Brain",
            category="Radiology",
            typical_cpt_codes=["70551", "70552", "70553"]
        )
        assert service.name == "MRI Brain"
        assert service.category == "Radiology"
        assert len(service.typical_cpt_codes) == 3


if __name__ == "__main__":
    # Run pytest with verbose output
    import subprocess
    result = subprocess.run(
        ["python3", "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    exit(result.returncode)