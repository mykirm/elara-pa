from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import os
from pathlib import Path

# Import your existing models
from models import Rule, CPTCode, ICDCode, AuthRequirement, RuleType
from models_enhanced import EnhancedRule, RuleCollection
from parsers.pdf_extractor import convert_pdf_to_markdown
from parsers.payer_rules.uhc_rules import parse_markdown_to_rules
from loaders.dual_parser_loader import dual_loader

app = FastAPI(
    title="Elara Prior Authorization API",
    description="Enhanced prior authorization with reasoning",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class PriorAuthRequest(BaseModel):
    cpt_codes: List[str]
    icd_codes: Optional[List[str]] = None
    patient_age: Optional[int] = None
    state: Optional[str] = None
    service_setting: Optional[str] = None

class PriorAuthResponse(BaseModel):
    requires_authorization: Optional[AuthRequirement]
    confidence_score: float
    applicable_rules: List[dict]  # Using dict for now since Rule serialization might be complex
    reasoning_path: List[str]
    geographic_exceptions: List[str] = []

class EnhancedPriorAuthRequest(BaseModel):
    cpt_codes: List[str]
    icd_codes: Optional[List[str]] = None
    patient_age: Optional[int] = None
    state: Optional[str] = None
    place_of_service: Optional[str] = None  # NEW: POS code
    provider_specialty: Optional[str] = None  # NEW: Provider specialty
    plan_type: Optional[str] = None  # NEW: Plan type

class EnhancedPriorAuthResponse(BaseModel):
    requires_authorization: bool
    auth_requirement: Optional[AuthRequirement]
    confidence_score: float
    primary_reason: str
    applicable_rules: List[dict]
    evaluation_details: List[dict]  # NEW: Detailed evaluation for each rule
    reasoning_path: List[str]

# Simple in-memory storage for now
loaded_rules: List[Rule] = []

def normalize_enum_value(value: str, enum_class) -> str:
    """Normalize enum values from JSON to proper enum format"""
    if isinstance(value, str):
        # Convert from lowercase to uppercase
        normalized = value.upper()
        # Handle specific enum mappings
        if enum_class == AuthRequirement:
            mapping = {
                'REQUIRED': 'REQUIRED',
                'NOT_REQUIRED': 'NOT_REQUIRED', 
                'CONDITIONAL': 'CONDITIONAL',
                'NOTIFICATION_ONLY': 'NOTIFICATION_ONLY'
            }
            return mapping.get(normalized, normalized)
        elif enum_class == RuleType:
            mapping = {
                'CPT_BASED': 'CPT_BASED',
                'DIAGNOSIS_BASED': 'DIAGNOSIS_BASED',
                'COMBINATION': 'COMBINATION',
                'SERVICE_BASED': 'SERVICE_BASED'
            }
            return mapping.get(normalized, normalized)
    return value

@app.on_event("startup")
async def load_rules():
    """Load existing processed rules on startup using dual parser loader"""
    global loaded_rules
    
    # Use dual parser loader for migration support
    loaded_rules = dual_loader.load_existing_rules()
    dual_loader.loaded_rules = loaded_rules  # Store in loader for evaluation
    
    # Get capabilities and log startup info
    capabilities = dual_loader.get_evaluation_capabilities()
    print(f"\n🚀 Elara Prior Authorization API Started")
    print(f"📊 Loaded {len(loaded_rules)} rules")
    print(f"🔧 Configuration:")
    for key, value in capabilities.items():
        print(f"   {key}: {value}")
    print(f"📝 Rule types loaded: {type(loaded_rules[0]).__name__ if loaded_rules else 'None'}")
    print("=" * 60)

@app.get("/")
async def root():
    capabilities = dual_loader.get_evaluation_capabilities()
    return {
        "message": "Elara Prior Authorization API",
        "rules_loaded": len(loaded_rules),
        "parser_mode": "Enhanced" if capabilities['enhanced_parser_enabled'] else "Original",
        "capabilities": capabilities
    }

@app.get("/capabilities")
async def get_capabilities():
    """Get current system capabilities and configuration"""
    capabilities = dual_loader.get_evaluation_capabilities()
    
    # Analyze loaded rules for enhanced features
    enhanced_features = {
        "rules_with_pos_restrictions": 0,
        "rules_with_diagnosis_exceptions": 0,
        "rules_with_age_restrictions": 0,
        "rules_with_geographic_exceptions": 0,
        "rules_with_conditional_logic": 0
    }
    
    if loaded_rules and hasattr(loaded_rules[0], 'place_of_service_restrictions'):
        # We have enhanced rules
        for rule in loaded_rules:
            if rule.place_of_service_restrictions:
                enhanced_features["rules_with_pos_restrictions"] += 1
            if rule.diagnosis_exceptions:
                enhanced_features["rules_with_diagnosis_exceptions"] += 1
            if rule.age_restrictions:
                enhanced_features["rules_with_age_restrictions"] += 1
            if rule.excluded_states or rule.included_states:
                enhanced_features["rules_with_geographic_exceptions"] += 1
            if rule.conditional_logic:
                enhanced_features["rules_with_conditional_logic"] += 1
    
    return {
        "system_capabilities": capabilities,
        "rules_loaded": len(loaded_rules),
        "rule_type": type(loaded_rules[0]).__name__ if loaded_rules else "None",
        "enhanced_features": enhanced_features,
        "available_endpoints": {
            "basic_evaluation": "/authorization/evaluate",
            "enhanced_evaluation": "/authorization/evaluate-enhanced",
            "smart_evaluation": "/authorization/evaluate-smart",
            "upload_basic": "/upload-pdf",
            "upload_enhanced": "/upload-pdf-enhanced"
        }
    }

@app.get("/rules")
async def get_rules():
    """Get all loaded rules"""
    # Convert rules to dict format for JSON serialization
    rules_dict = []
    for rule in loaded_rules:
        rule_dict = rule.model_dump()  # Pydantic v2 method
        rules_dict.append(rule_dict)
    return {"rules": rules_dict, "count": len(loaded_rules)}

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process a payer PDF"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Create uploads directory
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(exist_ok=True)
    
    # Save uploaded file
    upload_path = upload_dir / file.filename
    
    with open(upload_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Process with dual parser loader
    try:
        # Convert PDF to markdown
        markdown_text = convert_pdf_to_markdown(str(upload_path))
        
        # Process with dual parser
        extracted_rules = dual_loader.process_new_document(markdown_text, str(upload_path))
        
        # Add to loaded rules
        global loaded_rules
        loaded_rules.extend(extracted_rules)
        dual_loader.loaded_rules = loaded_rules
        
        # Analyze extracted features
        enhanced_features = {}
        if extracted_rules and hasattr(extracted_rules[0], 'place_of_service_restrictions'):
            enhanced_features = {
                "place_of_service_rules": sum(1 for r in extracted_rules if r.place_of_service_restrictions),
                "diagnosis_exceptions": sum(1 for r in extracted_rules if r.diagnosis_exceptions),
                "age_restrictions": sum(1 for r in extracted_rules if r.age_restrictions),
                "geographic_exceptions": sum(1 for r in extracted_rules if r.excluded_states or r.included_states),
                "conditional_logic": sum(1 for r in extracted_rules if r.conditional_logic)
            }
        
        return {
            "message": f"Processed {len(extracted_rules)} rules",
            "rules_extracted": len(extracted_rules),
            "parser_used": "Enhanced" if dual_loader.use_enhanced_parser else "Original",
            "enhanced_features": enhanced_features,
            "total_rules_loaded": len(loaded_rules)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

# Basic reasoning endpoint
@app.post("/authorization/evaluate", response_model=PriorAuthResponse)
async def evaluate_authorization(request: PriorAuthRequest):
    """Evaluate prior authorization request"""
    
    # Simple rule matching
    applicable_rules = []
    reasoning_path = []
    geographic_exceptions = []
    
    reasoning_path.append(f"Searching for rules matching CPT codes: {request.cpt_codes}")
    
    for rule in loaded_rules:
        # Check if any CPT codes match
        rule_cpt_codes = rule.cpt_codes
        if any(cpt in rule_cpt_codes for cpt in request.cpt_codes):
            # Check geographic exceptions
            if request.state and request.state in rule.excluded_states:
                reasoning_path.append(f"Rule excluded for state {request.state}")
                geographic_exceptions.append(request.state)
                continue
            
            applicable_rules.append(rule.model_dump())  # Convert to dict
            reasoning_path.append(f"Found applicable rule with CPT codes: {rule_cpt_codes}")
    
    if not applicable_rules:
        reasoning_path.append("No matching rules found - defaulting to not required")
        return PriorAuthResponse(
            requires_authorization=AuthRequirement.NOT_REQUIRED,
            confidence_score=0.3,
            applicable_rules=[],
            reasoning_path=reasoning_path,
            geographic_exceptions=geographic_exceptions
        )
    
    # Simple logic - if any rule requires auth, then auth required
    requires_auth = any(
        rule.get('auth_requirement') == AuthRequirement.REQUIRED.value 
        for rule in applicable_rules
    )
    
    auth_requirement = AuthRequirement.REQUIRED if requires_auth else AuthRequirement.NOT_REQUIRED
    reasoning_path.append(f"Final decision: {auth_requirement.value}")
    
    return PriorAuthResponse(
        requires_authorization=auth_requirement,
        confidence_score=0.8 if applicable_rules else 0.3,
        applicable_rules=applicable_rules,
        reasoning_path=reasoning_path,
        geographic_exceptions=geographic_exceptions
    )

# Enhanced evaluation endpoint with context-aware logic
@app.post("/authorization/evaluate-enhanced", response_model=EnhancedPriorAuthResponse)
async def evaluate_authorization_enhanced(request: EnhancedPriorAuthRequest):
    """Enhanced authorization evaluation with context-aware rule processing"""
    
    # Find applicable rules for all CPT codes
    applicable_rules = []
    evaluation_details = []
    reasoning_path = []
    
    reasoning_path.append(f"Enhanced evaluation for CPT codes: {request.cpt_codes}")
    
    for cpt_code in request.cpt_codes:
        reasoning_path.append(f"Evaluating CPT code: {cpt_code}")
        
        # Find rules matching this CPT code
        matching_rules = [rule for rule in loaded_rules if cpt_code in rule.cpt_codes]
        
        for rule in matching_rules:
            # Convert to enhanced rule for evaluation
            enhanced_rule = EnhancedRule.from_basic_rule(rule)
            
            # Evaluate with context
            evaluation = enhanced_rule.evaluate_authorization(
                patient_age=request.patient_age,
                diagnosis_codes=request.icd_codes or [],
                place_of_service=request.place_of_service,
                provider_specialty=request.provider_specialty,
                patient_state=request.state,
                plan_type=request.plan_type
            )
            
            evaluation_details.append({
                'rule_id': rule.rule_id,
                'cpt_code': cpt_code,
                'evaluation': evaluation,
                'rule_summary': f"{rule.service} - {rule.auth_requirement}"
            })
            
            applicable_rules.append(rule.model_dump())
            reasoning_path.append(f"Rule evaluation: {evaluation['reason']} (confidence: {evaluation['confidence']})")
    
    if not evaluation_details:
        reasoning_path.append("No applicable rules found")
        return EnhancedPriorAuthResponse(
            requires_authorization=False,
            auth_requirement=AuthRequirement.NOT_REQUIRED,
            confidence_score=0.3,
            primary_reason="No applicable rules found",
            applicable_rules=[],
            evaluation_details=[],
            reasoning_path=reasoning_path
        )
    
    # Determine final authorization requirement
    # If any evaluation requires auth, then auth is required
    auth_required_evaluations = [e for e in evaluation_details if e['evaluation']['auth_required']]
    
    if auth_required_evaluations:
        # Use the highest confidence "required" evaluation
        best_evaluation = max(auth_required_evaluations, key=lambda x: x['evaluation']['confidence'])
        requires_auth = True
        auth_requirement = AuthRequirement.REQUIRED
        primary_reason = best_evaluation['evaluation']['reason']
        confidence_score = best_evaluation['evaluation']['confidence']
        reasoning_path.append(f"Final decision: REQUIRED - {primary_reason}")
    else:
        # Use the highest confidence evaluation
        best_evaluation = max(evaluation_details, key=lambda x: x['evaluation']['confidence'])
        requires_auth = False
        auth_requirement = AuthRequirement.NOT_REQUIRED
        primary_reason = best_evaluation['evaluation']['reason']
        confidence_score = best_evaluation['evaluation']['confidence']
        reasoning_path.append(f"Final decision: NOT REQUIRED - {primary_reason}")
    
    return EnhancedPriorAuthResponse(
        requires_authorization=requires_auth,
        auth_requirement=auth_requirement,
        confidence_score=confidence_score,
        primary_reason=primary_reason,
        applicable_rules=applicable_rules,
        evaluation_details=evaluation_details,
        reasoning_path=reasoning_path
    )

@app.post("/upload-pdf-enhanced")
async def upload_pdf_enhanced(file: UploadFile = File(...)):
    """Upload and process PDF with enhanced parser (force enhanced mode)"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Create uploads directory
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(exist_ok=True)
    
    # Save uploaded file
    upload_path = upload_dir / file.filename
    
    with open(upload_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    try:
        # Convert PDF to markdown
        markdown_text = convert_pdf_to_markdown(str(upload_path))
        
        # Force enhanced processing
        from parsers.payer_rules.uhc_rules_enhanced import parse_markdown_to_enhanced_rules
        enhanced_rules = parse_markdown_to_enhanced_rules(markdown_text, str(upload_path))
        
        # Save enhanced rules
        from datetime import datetime
        output_path = Path("data/processed") / f"{file.filename.stem}_enhanced_rules_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_path, "w") as f:
            rules_data = [rule.model_dump() for rule in enhanced_rules]
            json.dump(rules_data, f, indent=2, default=str)
        
        # Add to loaded rules
        global loaded_rules
        loaded_rules.extend(enhanced_rules)
        dual_loader.loaded_rules = loaded_rules
        
        # Analyze enhanced features
        enhanced_features = {
            "place_of_service_rules": sum(1 for r in enhanced_rules if r.place_of_service_restrictions),
            "diagnosis_exceptions": sum(1 for r in enhanced_rules if r.diagnosis_exceptions),
            "age_restrictions": sum(1 for r in enhanced_rules if r.age_restrictions),
            "geographic_exceptions": sum(1 for r in enhanced_rules if r.excluded_states or r.included_states),
            "conditional_logic": sum(1 for r in enhanced_rules if r.conditional_logic)
        }
        
        return {
            "message": f"Enhanced processing completed",
            "rules_extracted": len(enhanced_rules),
            "parser_used": "Enhanced",
            "enhanced_features": enhanced_features,
            "output_file": str(output_path),
            "total_rules_loaded": len(loaded_rules)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhanced processing failed: {str(e)}")

@app.post("/authorization/evaluate-smart")
async def evaluate_authorization_smart(request: EnhancedPriorAuthRequest):
    """Smart authorization evaluation using dual parser loader"""
    try:
        # Use dual parser loader for evaluation
        evaluation_result = dual_loader.evaluate_authorization(
            cpt_codes=request.cpt_codes,
            patient_age=request.patient_age,
            diagnosis_codes=request.icd_codes or [],
            place_of_service=request.place_of_service,
            provider_specialty=request.provider_specialty,
            patient_state=request.state,
            plan_type=request.plan_type
        )
        
        return {
            "requires_authorization": evaluation_result['auth_required'],
            "confidence_score": evaluation_result['confidence'],
            "primary_reason": evaluation_result['reason'],
            "evaluation_method": evaluation_result['evaluation_method'],
            "rules_evaluated": evaluation_result['rules_evaluated'],
            "cpt_codes_evaluated": request.cpt_codes,
            "context_provided": {
                "patient_age": request.patient_age,
                "diagnosis_codes": len(request.icd_codes or []),
                "place_of_service": request.place_of_service,
                "state": request.state
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Smart evaluation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)