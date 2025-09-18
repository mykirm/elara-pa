import re
import json
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Import our models
try:
    from src.models import Rule, RuleType, AuthRequirement
except ImportError:
    # When running from FastAPI context
    from models import Rule, RuleType, AuthRequirement


def parse_markdown_to_rules(markdown_text: str, source_file: str = "unknown.pdf") -> List[Rule]:
    """Parse Markdown text into structured Rule objects.
    
    Args:
        markdown_text: Markdown text from PDF conversion
        source_file: Source PDF filename for provenance
        
    Returns:
        List of Rule objects extracted from the text
        
    Note:
        - Uses regex for deterministic parsing of codes and patterns
        - Marks complex narrative sections for LLM processing
        - Handles state-specific exceptions and diagnosis requirements
    """
    rules = []
    
    # Split text into lines for line-by-line processing
    lines = markdown_text.split('\n')
    
    # Track current context as we parse
    current_category = None
    current_service = None
    current_page = 1
    
    # Regex patterns for extraction
    cpt_pattern = r'\b(\d{5})\b'  # 5-digit CPT codes
    cpt_range_pattern = r'\b(\d{5})\s*[-–]\s*(\d{5})\b'  # CPT ranges
    hcpcs_pattern = r'\b([A-V]\d{4})\b'  # HCPCS codes
    icd_pattern = r'\b([A-Z]\d{2}(?:\.\d{1,4})?)\b'  # ICD-10 codes
    state_pattern = r'\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC)\b'
    page_pattern = r'Page\s+(\d+)'
    
    # Keywords indicating authorization requirements
    auth_required_keywords = ['prior authorization required', 'requires prior authorization', 'PA required']
    auth_not_required_keywords = ['no prior authorization', 'not required', 'no PA required']
    notification_keywords = ['notification only', 'notify only']
    
    for line_num, line in enumerate(lines, start=1):
        # Update page number if found
        page_match = re.search(page_pattern, line)
        if page_match:
            current_page = int(page_match.group(1))
        
        # Detect category headers (usually in caps or with specific formatting)
        if line.strip() and line.isupper() and len(line.strip()) > 5:
            current_category = line.strip()
            continue
        
        # Detect service names (often before code listings)
        if line.strip() and not any(re.search(p, line) for p in [cpt_pattern, hcpcs_pattern]):
            # Heuristic: lines with title case might be service names
            words = line.strip().split()
            if len(words) > 1 and words[0][0].isupper():
                current_service = line.strip()
        
        # Extract CPT codes and ranges
        cpt_matches = re.findall(cpt_pattern, line)
        cpt_range_matches = re.findall(cpt_range_pattern, line)
        hcpcs_matches = re.findall(hcpcs_pattern, line)
        
        # If we found codes, create rules
        all_codes = list(cpt_matches) + list(hcpcs_matches)
        
        if all_codes or cpt_range_matches:
            # Determine authorization requirement from context
            auth_requirement = AuthRequirement.CONDITIONAL  # Default
            line_lower = line.lower()
            
            if any(keyword in line_lower for keyword in auth_required_keywords):
                auth_requirement = AuthRequirement.REQUIRED
            elif any(keyword in line_lower for keyword in auth_not_required_keywords):
                auth_requirement = AuthRequirement.NOT_REQUIRED
            elif any(keyword in line_lower for keyword in notification_keywords):
                auth_requirement = AuthRequirement.NOTIFICATION_ONLY
            
            # Extract state exceptions
            state_matches = re.findall(state_pattern, line)
            excluded_states = []
            included_states = []
            
            # Simple heuristic: if "except" or "excluding" appears before states
            if 'except' in line_lower or 'excluding' in line_lower:
                excluded_states = state_matches
            elif 'only in' in line_lower or 'limited to' in line_lower:
                included_states = state_matches
            
            # Extract ICD codes if present
            icd_matches = re.findall(icd_pattern, line)
            
            # Check for complex narrative requiring LLM
            requires_llm = False
            narrative_text = None
            
            # Complex narrative indicators
            complex_indicators = [
                'when used for', 'in combination with', 'following criteria',
                'must meet', 'clinical indications', 'medical necessity'
            ]
            
            if any(indicator in line_lower for indicator in complex_indicators):
                requires_llm = True
                narrative_text = line.strip()
                # TODO: This narrative would be sent to an LLM for structured extraction
                # Prompt template:
                # "Extract authorization requirements from: {narrative_text}
                #  Return: conditions, age_limits, quantity_limits, clinical_criteria"
            
            # Handle CPT ranges
            if cpt_range_matches:
                for start_code, end_code in cpt_range_matches:
                    all_codes.append(f"RANGE_{start_code}_{end_code}")
            
            # Create Rule object for each code group
            if all_codes:
                rule = Rule(
                    rule_type=RuleType.CPT_BASED if not icd_matches else RuleType.COMBINATION,
                    auth_requirement=auth_requirement,
                    payer="UnitedHealthcare",  # Default for this parser
                    category=current_category,
                    service=current_service,
                    cpt_codes=all_codes,
                    icd_codes=icd_matches,
                    excluded_states=excluded_states,
                    included_states=included_states,
                    narrative_text=narrative_text,
                    requires_llm_processing=requires_llm,
                    source_file=source_file,
                    source_page=current_page,
                    source_line=line_num,
                    confidence_score=0.8 if not requires_llm else 0.5
                )
                
                rules.append(rule)
                
                # Debug output
                if len(rules) % 10 == 0:
                    print(f"Parsed {len(rules)} rules so far...")
    
    # Post-processing: merge related rules
    rules = merge_related_rules(rules)
    
    # Save processed rules
    save_processed_rules(rules, source_file)
    
    print(f"Total rules extracted: {len(rules)}")
    return rules


def merge_related_rules(rules: List[Rule]) -> List[Rule]:
    """Merge rules that refer to the same service/category.
    
    Args:
        rules: List of Rule objects
        
    Returns:
        List of merged Rule objects
        
    Note:
        - Combines rules with same service and category
        - Preserves all CPT codes and conditions
    """
    merged_rules = {}
    
    for rule in rules:
        # Create a key for grouping related rules
        key = (
            rule.payer,
            rule.category,
            rule.service,
            rule.auth_requirement.value
        )
        
        if key in merged_rules:
            # Merge codes and conditions
            existing = merged_rules[key]
            existing.cpt_codes.extend(rule.cpt_codes)
            existing.icd_codes.extend(rule.icd_codes)
            existing.excluded_states.extend(rule.excluded_states)
            existing.included_states.extend(rule.included_states)
            
            # Deduplicate
            existing.cpt_codes = list(set(existing.cpt_codes))
            existing.icd_codes = list(set(existing.icd_codes))
            existing.excluded_states = list(set(existing.excluded_states))
            existing.included_states = list(set(existing.included_states))
            
            # Update confidence (take minimum)
            if rule.confidence_score and existing.confidence_score:
                existing.confidence_score = min(existing.confidence_score, rule.confidence_score)
        else:
            merged_rules[key] = rule
    
    return list(merged_rules.values())


def save_processed_rules(rules: List[Rule], source_file: str):
    """Save processed rules to data/processed/ directory.
    
    Args:
        rules: List of Rule objects
        source_file: Source filename
    """
    base_name = Path(source_file).stem
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = f"data/processed/{base_name}_rules_{timestamp}.json"
    
    os.makedirs("data/processed", exist_ok=True)
    
    # Convert rules to JSON-serializable format
    rules_data = []
    for rule in rules:
        rule_dict = rule.model_dump(mode='json')
        # Add hyperedge representation
        rule_dict['hyperedge'] = rule.to_hyperedge()
        rules_data.append(rule_dict)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(rules_data, f, indent=2, default=str)
    
    print(f"Saved {len(rules)} processed rules to: {output_path}")
    
    # Also save a summary
    summary_path = f"data/processed/{base_name}_summary_{timestamp}.txt"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(f"UnitedHealthcare Prior Authorization Rules Summary\n")
        f.write(f"=" * 50 + "\n\n")
        f.write(f"Source: {source_file}\n")
        f.write(f"Extraction Date: {datetime.now().isoformat()}\n")
        f.write(f"Total Rules: {len(rules)}\n\n")
        
        # Group by category
        categories = {}
        for rule in rules:
            cat = rule.category or "Uncategorized"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(rule)
        
        f.write(f"Rules by Category:\n")
        for cat, cat_rules in categories.items():
            f.write(f"  {cat}: {len(cat_rules)} rules\n")
            
            # Show auth requirement breakdown
            auth_breakdown = {}
            for r in cat_rules:
                auth_breakdown[r.auth_requirement.value] = auth_breakdown.get(r.auth_requirement.value, 0) + 1
            
            for auth_type, count in auth_breakdown.items():
                f.write(f"    - {auth_type}: {count}\n")
        
        f.write(f"\n\nRules requiring LLM processing: {sum(1 for r in rules if r.requires_llm_processing)}\n")
    
    print(f"Saved summary to: {summary_path}")


# LLM Prompt Templates (for future use)
LLM_PROMPTS = {
    'extract_clinical_criteria': """
Extract clinical criteria from the following prior authorization text:

Text: {narrative_text}

Return a JSON object with:
- conditions: List of medical conditions or diagnoses required
- age_restrictions: Any age-based requirements (min_age, max_age)
- quantity_limits: Limits on frequency or quantity
- clinical_requirements: Specific clinical criteria that must be met
- prior_treatments: Any required prior treatments or step therapy

Example response:
{{
    "conditions": ["chronic pain", "failed conservative therapy"],
    "age_restrictions": {{"min_age": 18}},
    "quantity_limits": {{"max_per_year": 2}},
    "clinical_requirements": ["documented MRI findings"],
    "prior_treatments": ["6 weeks physical therapy"]
}}
""",
    
    'extract_state_exceptions': """
Identify state-specific exceptions from the following text:

Text: {narrative_text}

Return a JSON object with:
- excluded_states: List of state codes where the rule does NOT apply
- included_states: List of state codes where the rule ONLY applies
- state_specific_requirements: Any state-specific requirements

Example response:
{{
    "excluded_states": ["CA", "NY"],
    "included_states": [],
    "state_specific_requirements": {{
        "TX": "Requires additional documentation",
        "FL": "Limited to Medicare Advantage plans"
    }}
}}
""",
    
    'extract_complex_rule': """
Parse the following complex authorization rule:

Text: {narrative_text}

Context:
- Category: {category}
- Service: {service}
- CPT Codes: {cpt_codes}

Extract all authorization requirements, conditions, and exceptions.
Return a structured JSON with all relevant fields.
"""
}


def get_llm_prompt(prompt_type: str, **kwargs) -> str:
    """Get formatted LLM prompt for complex extraction.
    
    Args:
        prompt_type: Type of prompt from LLM_PROMPTS
        **kwargs: Variables to format into the prompt
        
    Returns:
        Formatted prompt string
        
    Note:
        - This function prepares prompts but doesn't call LLM
        - Actual LLM integration would happen in a separate module
    """
    if prompt_type not in LLM_PROMPTS:
        raise ValueError(f"Unknown prompt type: {prompt_type}")
    
    return LLM_PROMPTS[prompt_type].format(**kwargs)