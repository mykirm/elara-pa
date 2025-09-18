"""Enhanced rule loader with dual parser support for production migration."""

import os
import json
from pathlib import Path
from typing import List, Union
from datetime import datetime

try:
    from src.models import Rule, AuthRequirement, RuleType
    from src.models_enhanced import EnhancedRule
    from src.parsers.payer_rules.uhc_rules import parse_markdown_to_rules
    from src.parsers.payer_rules.uhc_rules_enhanced import parse_markdown_to_enhanced_rules
except ImportError:
    from models import Rule, AuthRequirement, RuleType
    from models_enhanced import EnhancedRule
    from parsers.payer_rules.uhc_rules import parse_markdown_to_rules
    from parsers.payer_rules.uhc_rules_enhanced import parse_markdown_to_enhanced_rules


class DualParserLoader:
    """Rule loader supporting both original and enhanced parsers for migration"""
    
    def __init__(self):
        self.use_enhanced_parser = os.getenv('USE_ENHANCED_PARSER', 'false').lower() == 'true'
        self.enable_enhanced_evaluation = os.getenv('ENABLE_ENHANCED_EVALUATION', 'true').lower() == 'true'
        self.fallback_to_original = os.getenv('FALLBACK_TO_ORIGINAL', 'true').lower() == 'true'
        self.loaded_rules: List[Union[Rule, EnhancedRule]] = []
        
        print(f"DualParserLoader initialized:")
        print(f"  Enhanced parser: {self.use_enhanced_parser}")
        print(f"  Enhanced evaluation: {self.enable_enhanced_evaluation}")
        print(f"  Fallback enabled: {self.fallback_to_original}")
        
    def load_existing_rules(self) -> List[Union[Rule, EnhancedRule]]:
        """Load existing processed rules with parser selection"""
        rules = []
        processed_dir = Path("data/processed")
        
        if not processed_dir.exists():
            print("No processed directory found")
            return rules
            
        # Prioritize enhanced rules if enhanced parser is enabled
        if self.use_enhanced_parser:
            # Look for enhanced rules first
            enhanced_files = list(processed_dir.glob("*_enhanced_rules_*.json"))
            if enhanced_files:
                print(f"Loading enhanced rules from {len(enhanced_files)} files...")
                for json_file in enhanced_files:
                    rules.extend(self._load_enhanced_rules_from_file(json_file))
                
                if rules:
                    print(f"Loaded {len(rules)} enhanced rules")
                    return rules
            
            print("No enhanced rules found, converting basic rules to enhanced...")
            
        # Load basic rules (either as fallback or primary)
        basic_files = [f for f in processed_dir.glob("*_rules_*.json") 
                      if "_enhanced_rules_" not in f.name]
        
        print(f"Loading basic rules from {len(basic_files)} files...")
        for json_file in basic_files:
            file_rules = self._load_basic_rules_from_file(json_file)
            
            if self.use_enhanced_parser:
                # Convert basic rules to enhanced rules
                enhanced_rules = []
                for basic_rule in file_rules:
                    enhanced_rule = EnhancedRule.from_basic_rule(basic_rule)
                    enhanced_rules.append(enhanced_rule)
                rules.extend(enhanced_rules)
                print(f"Converted {len(file_rules)} basic rules to enhanced rules from {json_file}")
            else:
                rules.extend(file_rules)
                print(f"Loaded {len(file_rules)} basic rules from {json_file}")
                
        print(f"Total rules loaded: {len(rules)} ({'Enhanced' if self.use_enhanced_parser else 'Basic'} format)")
        return rules
    
    def _load_enhanced_rules_from_file(self, json_file: Path) -> List[EnhancedRule]:
        """Load enhanced rules from JSON file"""
        rules = []
        try:
            with open(json_file) as f:
                rules_data = json.load(f)
                
            for rule_data in rules_data:
                # Handle enhanced rule loading with all fields
                rule_data = self._normalize_rule_data(rule_data)
                rule = EnhancedRule(**rule_data)
                rules.append(rule)
                
        except Exception as e:
            print(f"Error loading enhanced rules from {json_file}: {e}")
            
        return rules
    
    def _load_basic_rules_from_file(self, json_file: Path) -> List[Rule]:
        """Load basic rules from JSON file"""
        rules = []
        try:
            with open(json_file) as f:
                rules_data = json.load(f)
                
            for rule_data in rules_data:
                rule_data = self._normalize_rule_data(rule_data)
                rule = Rule(**rule_data)
                rules.append(rule)
                
        except Exception as e:
            print(f"Error loading basic rules from {json_file}: {e}")
            
        return rules
    
    def process_new_document(self, markdown_text: str, source_file: str) -> List[Union[Rule, EnhancedRule]]:
        """Process new document with selected parser"""
        try:
            if self.use_enhanced_parser:
                print(f"Processing {source_file} with enhanced parser...")
                enhanced_rules = parse_markdown_to_enhanced_rules(markdown_text, source_file)
                
                # Save enhanced rules
                output_path = Path("data/processed") / f"{Path(source_file).stem}_enhanced_rules_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                output_path.parent.mkdir(exist_ok=True)
                
                with open(output_path, "w") as f:
                    rules_data = [rule.model_dump() for rule in enhanced_rules]
                    json.dump(rules_data, f, indent=2, default=str)
                
                # Log enhanced features found
                pos_count = sum(1 for rule in enhanced_rules if rule.place_of_service_restrictions)
                dx_count = sum(1 for rule in enhanced_rules if rule.diagnosis_exceptions)
                age_count = sum(1 for rule in enhanced_rules if rule.age_restrictions)
                geo_count = sum(1 for rule in enhanced_rules if rule.excluded_states or rule.included_states)
                cond_count = sum(1 for rule in enhanced_rules if rule.conditional_logic)
                
                print(f"Enhanced parser extracted {len(enhanced_rules)} rules:")
                print(f"  - {pos_count} with place of service restrictions")
                print(f"  - {dx_count} with diagnosis exceptions") 
                print(f"  - {age_count} with age restrictions")
                print(f"  - {geo_count} with geographic restrictions")
                print(f"  - {cond_count} with conditional logic")
                
                return enhanced_rules
                
            else:
                print(f"Processing {source_file} with original parser...")
                basic_rules = parse_markdown_to_rules(markdown_text, source_file)
                
                # Save basic rules
                output_path = Path("data/processed") / f"{Path(source_file).stem}_rules_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                output_path.parent.mkdir(exist_ok=True)
                
                with open(output_path, "w") as f:
                    rules_data = [rule.model_dump() for rule in basic_rules]
                    json.dump(rules_data, f, indent=2, default=str)
                
                print(f"Original parser extracted {len(basic_rules)} rules")
                return basic_rules
                
        except Exception as e:
            print(f"Error processing document with {'enhanced' if self.use_enhanced_parser else 'original'} parser: {e}")
            
            # Fallback to original parser if enhanced fails
            if self.use_enhanced_parser and self.fallback_to_original:
                print("Falling back to original parser...")
                try:
                    return parse_markdown_to_rules(markdown_text, source_file)
                except Exception as fallback_error:
                    print(f"Fallback parser also failed: {fallback_error}")
                    raise
            else:
                raise
    
    def get_evaluation_capabilities(self) -> dict:
        """Get current evaluation capabilities"""
        return {
            'enhanced_parser_enabled': self.use_enhanced_parser,
            'enhanced_evaluation_enabled': self.enable_enhanced_evaluation,
            'supports_place_of_service': self.use_enhanced_parser,
            'supports_diagnosis_exceptions': self.use_enhanced_parser,
            'supports_age_restrictions': self.use_enhanced_parser,
            'supports_conditional_logic': self.use_enhanced_parser,
            'supports_provider_restrictions': self.use_enhanced_parser,
            'context_aware_evaluation': self.use_enhanced_parser and self.enable_enhanced_evaluation,
            'fallback_enabled': self.fallback_to_original
        }
    
    def evaluate_authorization(self, cpt_codes: List[str], **evaluation_context) -> dict:
        """Evaluate authorization using appropriate method"""
        applicable_rules = []
        
        # Find applicable rules
        for rule in self.loaded_rules:
            if any(cpt in rule.cpt_codes for cpt in cpt_codes):
                applicable_rules.append(rule)
        
        if not applicable_rules:
            return {
                'auth_required': False,
                'reason': 'No applicable rules found',
                'confidence': 0.5,
                'evaluation_method': 'none'
            }
        
        # Use enhanced evaluation if available and enabled
        if self.enable_enhanced_evaluation and applicable_rules and isinstance(applicable_rules[0], EnhancedRule):
            return self._enhanced_evaluation(applicable_rules, evaluation_context)
        else:
            return self._basic_evaluation(applicable_rules, evaluation_context)
    
    def _enhanced_evaluation(self, rules: List[EnhancedRule], context: dict) -> dict:
        """Enhanced context-aware evaluation"""
        evaluations = []
        
        for rule in rules:
            evaluation = rule.evaluate_authorization(**context)
            evaluations.append({
                'rule': rule,
                'evaluation': evaluation
            })
        
        # If any rule requires auth, auth is required
        required_evaluations = [e for e in evaluations if e['evaluation']['auth_required']]
        
        if required_evaluations:
            best = max(required_evaluations, key=lambda x: x['evaluation']['confidence'])
            return {
                'auth_required': True,
                'reason': best['evaluation']['reason'],
                'confidence': best['evaluation']['confidence'],
                'evaluation_method': 'enhanced',
                'rules_evaluated': len(rules)
            }
        else:
            best = max(evaluations, key=lambda x: x['evaluation']['confidence'])
            return {
                'auth_required': False,
                'reason': best['evaluation']['reason'],
                'confidence': best['evaluation']['confidence'],
                'evaluation_method': 'enhanced',
                'rules_evaluated': len(rules)
            }
    
    def _basic_evaluation(self, rules: List[Union[Rule, EnhancedRule]], context: dict) -> dict:
        """Basic rule evaluation"""
        # Simple logic: if any rule requires auth, auth is required
        requires_auth = any(rule.auth_requirement == AuthRequirement.REQUIRED for rule in rules)
        
        return {
            'auth_required': requires_auth,
            'reason': 'Basic rule match' if requires_auth else 'No authorization required',
            'confidence': 0.8 if rules else 0.3,
            'evaluation_method': 'basic',
            'rules_evaluated': len(rules)
        }
    
    def _normalize_rule_data(self, rule_data: dict) -> dict:
        """Normalize rule data for loading"""
        # Normalize enum values
        if 'auth_requirement' in rule_data and rule_data['auth_requirement']:
            rule_data['auth_requirement'] = self._normalize_enum_value(
                rule_data['auth_requirement'], AuthRequirement
            )
        if 'rule_type' in rule_data and rule_data['rule_type']:
            rule_data['rule_type'] = self._normalize_enum_value(
                rule_data['rule_type'], RuleType
            )
        
        # Handle missing required fields
        if not rule_data.get('rule_type'):
            rule_data['rule_type'] = 'CPT_BASED'
        if not rule_data.get('auth_requirement'):
            rule_data['auth_requirement'] = 'NOT_REQUIRED'
        if not rule_data.get('payer'):
            rule_data['payer'] = 'Unknown'
        
        return rule_data
    
    def _normalize_enum_value(self, value: str, enum_class) -> str:
        """Normalize enum values from JSON to proper enum format"""
        if isinstance(value, str):
            normalized = value.upper()
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


# Global loader instance
dual_loader = DualParserLoader()