#!/usr/bin/env python3
"""
Interactive Prior Authorization System
=====================================

A command-line interface for manually testing prior authorization decisions
using the PA hypergraph system with real UHC rules.

Usage: python interactive_pa_system.py
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.models import Rule, AuthRequirement, RuleType
    from src.parsers.payer_rules.uhc_rules import parse_markdown_to_rules
except ImportError:
    print("Import error - running from project root")
    from models import Rule, AuthRequirement, RuleType
    from parsers.payer_rules.uhc_rules import parse_markdown_to_rules


class InteractivePASystem:
    """Interactive Prior Authorization Decision System"""
    
    def __init__(self):
        self.rules = []
        self.session_log = []
        self.load_rules()
    
    def load_rules(self):
        """Load existing rules from processed data"""
        processed_dir = Path("data/processed")
        
        # Look for latest UHC rules file
        rule_files = list(processed_dir.glob("*rules*.json"))
        if rule_files:
            # Use the most recent rules file
            latest_file = max(rule_files, key=os.path.getctime)
            print(f"🔄 Loading rules from: {latest_file.name}")
            
            try:
                with open(latest_file, 'r') as f:
                    rules_data = json.load(f)
                
                # Convert to Rule objects
                for rule_data in rules_data:
                    try:
                        rule = Rule(**rule_data)
                        self.rules.append(rule)
                    except Exception as e:
                        # Skip invalid rules
                        continue
                
                print(f"✅ Loaded {len(self.rules)} authorization rules")
            except Exception as e:
                print(f"❌ Error loading rules: {e}")
                self.rules = []
        else:
            print("⚠️  No rule files found. Starting with empty rule set.")
    
    def display_header(self):
        """Display system header"""
        print("\n" + "="*80)
        print("🏥 INTERACTIVE PRIOR AUTHORIZATION SYSTEM")
        print("="*80)
        print(f"📋 Rules Loaded: {len(self.rules)}")
        print(f"🕐 Session Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
    
    def get_patient_info(self) -> Dict[str, Any]:
        """Collect patient information"""
        print("\n📋 PATIENT INFORMATION")
        print("-" * 30)
        
        patient_info = {}
        
        # Basic demographics
        patient_info['patient_id'] = input("Patient ID (optional): ").strip() or f"PATIENT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        patient_info['age'] = self.get_numeric_input("Patient Age: ", required=True)
        patient_info['state'] = input("Patient State (2-letter code, e.g., CA): ").strip().upper()
        
        # Insurance info
        print("\n💳 Insurance Information:")
        patient_info['payer'] = input("Insurance Payer (default: UnitedHealthcare): ").strip() or "UnitedHealthcare"
        patient_info['plan_type'] = input("Plan Type (HMO/PPO/POS): ").strip().upper()
        
        return patient_info
    
    def get_procedure_info(self) -> Dict[str, Any]:
        """Collect procedure information"""
        print("\n🏥 PROCEDURE INFORMATION")
        print("-" * 30)
        
        procedure_info = {}
        
        # CPT codes
        print("CPT/HCPCS Codes (enter one per line, empty line to finish):")
        cpt_codes = []
        while True:
            code = input("CPT Code: ").strip()
            if not code:
                break
            if len(code) == 5 and code.isdigit():
                cpt_codes.append(code)
                print(f"  ✅ Added CPT: {code}")
            elif len(code) == 5 and code[0].isalpha():
                cpt_codes.append(code.upper())
                print(f"  ✅ Added HCPCS: {code.upper()}")
            else:
                print(f"  ⚠️  Invalid format: {code} (should be 5 digits or letter+4 digits)")
        
        procedure_info['cpt_codes'] = cpt_codes
        
        # Diagnosis codes
        print("\nICD-10 Diagnosis Codes (enter one per line, empty line to finish):")
        icd_codes = []
        while True:
            code = input("ICD Code: ").strip().upper()
            if not code:
                break
            icd_codes.append(code)
            print(f"  ✅ Added ICD: {code}")
        
        procedure_info['icd_codes'] = icd_codes
        
        # Place of service
        print("\n🏢 Place of Service:")
        print("1. Office (11)")
        print("2. Outpatient Hospital (22)")
        print("3. Inpatient Hospital (21)")
        print("4. Ambulatory Surgery Center (24)")
        print("5. Other")
        
        pos_choice = input("Select place of service (1-5): ").strip()
        pos_map = {
            '1': ('11', 'Office'),
            '2': ('22', 'Outpatient Hospital'),
            '3': ('21', 'Inpatient Hospital'),
            '4': ('24', 'Ambulatory Surgery Center'),
            '5': ('99', 'Other')
        }
        
        if pos_choice in pos_map:
            procedure_info['place_of_service'] = pos_map[pos_choice][0]
            procedure_info['place_of_service_desc'] = pos_map[pos_choice][1]
        else:
            procedure_info['place_of_service'] = '99'
            procedure_info['place_of_service_desc'] = 'Other'
        
        # Provider info
        procedure_info['provider_specialty'] = input("Provider Specialty (optional): ").strip()
        
        return procedure_info
    
    def evaluate_authorization(self, patient_info: Dict, procedure_info: Dict) -> Dict[str, Any]:
        """Evaluate prior authorization requirements"""
        
        evaluation = {
            'patient_info': patient_info,
            'procedure_info': procedure_info,
            'matching_rules': [],
            'authorization_required': False,
            'authorization_type': 'NOT_REQUIRED',
            'reasons': [],
            'recommendations': [],
            'timestamp': datetime.now().isoformat()
        }
        
        print("\n🔍 EVALUATING AUTHORIZATION REQUIREMENTS...")
        print("-" * 50)
        
        # Find matching rules
        for rule in self.rules:
            matches = self.check_rule_match(rule, patient_info, procedure_info)
            if matches['is_match']:
                evaluation['matching_rules'].append({
                    'rule': rule,
                    'match_details': matches,
                    'rule_summary': str(rule)
                })
        
        # Determine authorization requirement
        if evaluation['matching_rules']:
            # If any rule requires authorization, it's required
            auth_requirements = [r['rule'].auth_requirement for r in evaluation['matching_rules']]
            
            if AuthRequirement.REQUIRED in auth_requirements:
                evaluation['authorization_required'] = True
                evaluation['authorization_type'] = 'REQUIRED'
                evaluation['reasons'].append("Procedure requires prior authorization per payer rules")
            elif AuthRequirement.CONDITIONAL in auth_requirements:
                evaluation['authorization_required'] = True
                evaluation['authorization_type'] = 'CONDITIONAL'
                evaluation['reasons'].append("Procedure may require authorization based on specific conditions")
            elif AuthRequirement.NOTIFICATION_ONLY in auth_requirements:
                evaluation['authorization_type'] = 'NOTIFICATION_ONLY'
                evaluation['reasons'].append("Notification to payer required, but no prior authorization")
            
            # Add specific rule-based reasons
            for match in evaluation['matching_rules']:
                rule = match['rule']
                if rule.clinical_criteria:
                    evaluation['reasons'].append(f"Clinical criteria: {rule.clinical_criteria}")
                if rule.excluded_states and patient_info.get('state') in rule.excluded_states:
                    evaluation['reasons'].append(f"State exclusion applies: {patient_info.get('state')}")
        
        # Generate recommendations
        self.generate_recommendations(evaluation)
        
        return evaluation
    
    def check_rule_match(self, rule: Rule, patient_info: Dict, procedure_info: Dict) -> Dict[str, Any]:
        """Check if a rule matches the given patient/procedure"""
        
        match_details = {
            'is_match': False,
            'cpt_match': False,
            'icd_match': False,
            'payer_match': False,
            'state_applicable': True,
            'age_applicable': True,
            'matched_cpt_codes': [],
            'matched_icd_codes': [],
            'exclusion_reasons': []
        }
        
        # Check payer
        if rule.payer.lower() in patient_info.get('payer', '').lower():
            match_details['payer_match'] = True
        
        # Check CPT codes
        patient_cpts = set(procedure_info.get('cpt_codes', []))
        rule_cpts = set(rule.cpt_codes)
        
        if patient_cpts.intersection(rule_cpts):
            match_details['cpt_match'] = True
            match_details['matched_cpt_codes'] = list(patient_cpts.intersection(rule_cpts))
        
        # Check ICD codes (if rule has ICD requirements)
        if rule.icd_codes:
            patient_icds = set(procedure_info.get('icd_codes', []))
            rule_icds = set(rule.icd_codes)
            
            if patient_icds.intersection(rule_icds):
                match_details['icd_match'] = True
                match_details['matched_icd_codes'] = list(patient_icds.intersection(rule_icds))
        else:
            # No ICD requirement means it matches
            match_details['icd_match'] = True
        
        # Check state exclusions
        patient_state = patient_info.get('state', '')
        if rule.excluded_states and patient_state in rule.excluded_states:
            match_details['state_applicable'] = False
            match_details['exclusion_reasons'].append(f"State {patient_state} is excluded")
        
        # Check age restrictions
        patient_age = patient_info.get('age')
        if patient_age:
            if rule.age_min and patient_age < rule.age_min:
                match_details['age_applicable'] = False
                match_details['exclusion_reasons'].append(f"Patient age {patient_age} below minimum {rule.age_min}")
            if rule.age_max and patient_age > rule.age_max:
                match_details['age_applicable'] = False
                match_details['exclusion_reasons'].append(f"Patient age {patient_age} above maximum {rule.age_max}")
        
        # Overall match determination
        match_details['is_match'] = (
            match_details['payer_match'] and
            match_details['cpt_match'] and
            match_details['icd_match'] and
            match_details['state_applicable'] and
            match_details['age_applicable']
        )
        
        return match_details
    
    def generate_recommendations(self, evaluation: Dict):
        """Generate actionable recommendations"""
        
        if evaluation['authorization_required']:
            evaluation['recommendations'].extend([
                "📞 Contact payer for prior authorization",
                "📋 Gather required clinical documentation",
                "⏰ Submit authorization request before procedure"
            ])
            
            # Specific recommendations based on rules
            for match in evaluation['matching_rules']:
                rule = match['rule']
                if rule.clinical_criteria:
                    evaluation['recommendations'].append(f"📝 Document: {rule.clinical_criteria}")
        else:
            evaluation['recommendations'].append("✅ No prior authorization required - proceed with procedure")
    
    def display_results(self, evaluation: Dict):
        """Display authorization evaluation results"""
        
        print("\n" + "="*80)
        print("🎯 PRIOR AUTHORIZATION DECISION")
        print("="*80)
        
        # Summary
        auth_status = "🔴 REQUIRED" if evaluation['authorization_required'] else "🟢 NOT REQUIRED"
        print(f"\n📊 Authorization Status: {auth_status}")
        print(f"📋 Authorization Type: {evaluation['authorization_type']}")
        
        # Matching rules
        if evaluation['matching_rules']:
            print(f"\n🔍 Matching Rules Found: {len(evaluation['matching_rules'])}")
            for i, match in enumerate(evaluation['matching_rules'], 1):
                rule = match['rule']
                print(f"\n  Rule {i}:")
                print(f"    Service: {rule.service or 'General'}")
                print(f"    CPT Codes: {', '.join(match['match_details']['matched_cpt_codes'])}")
                print(f"    Authorization: {rule.auth_requirement.value}")
                if rule.clinical_criteria:
                    print(f"    Criteria: {rule.clinical_criteria}")
        else:
            print("\n🔍 No specific rules found - using default policy")
        
        # Reasons
        if evaluation['reasons']:
            print(f"\n📝 Reasons:")
            for reason in evaluation['reasons']:
                print(f"  • {reason}")
        
        # Recommendations
        if evaluation['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in evaluation['recommendations']:
                print(f"  • {rec}")
        
        print("\n" + "="*80)
    
    def save_session(self, evaluation: Dict):
        """Save session results"""
        session_file = f"data/processed/pa_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            # Convert Rule objects to dicts for JSON serialization
            evaluation_copy = evaluation.copy()
            for match in evaluation_copy['matching_rules']:
                match['rule'] = match['rule'].__dict__
            
            with open(session_file, 'w') as f:
                json.dump(evaluation_copy, f, indent=2, default=str)
            
            print(f"\n💾 Session saved to: {session_file}")
        except Exception as e:
            print(f"\n❌ Error saving session: {e}")
    
    def get_numeric_input(self, prompt: str, required: bool = False) -> Optional[int]:
        """Get numeric input with validation"""
        while True:
            value = input(prompt).strip()
            if not value and not required:
                return None
            try:
                return int(value)
            except ValueError:
                print("  ⚠️  Please enter a valid number")
    
    def run_interactive_session(self):
        """Run a complete interactive PA evaluation session"""
        
        self.display_header()
        
        try:
            # Collect information
            patient_info = self.get_patient_info()
            procedure_info = self.get_procedure_info()
            
            # Evaluate authorization
            evaluation = self.evaluate_authorization(patient_info, procedure_info)
            
            # Display results
            self.display_results(evaluation)
            
            # Save session
            save_choice = input("\n💾 Save this session? (y/n): ").strip().lower()
            if save_choice in ['y', 'yes']:
                self.save_session(evaluation)
            
            return evaluation
            
        except KeyboardInterrupt:
            print("\n\n👋 Session cancelled by user")
            return None
        except Exception as e:
            print(f"\n❌ Error during session: {e}")
            return None
    
    def run_quick_test(self):
        """Run quick test with sample data"""
        print("\n🧪 QUICK TEST MODE")
        print("Using sample data for demonstration...")
        
        # Sample patient
        patient_info = {
            'patient_id': 'TEST_001',
            'age': 45,
            'state': 'CA',
            'payer': 'UnitedHealthcare',
            'plan_type': 'PPO'
        }
        
        # Sample procedure
        procedure_info = {
            'cpt_codes': ['27447'],  # Arthroplasty
            'icd_codes': ['M16.9'],  # Osteoarthritis
            'place_of_service': '22',
            'place_of_service_desc': 'Outpatient Hospital',
            'provider_specialty': 'Orthopedic Surgery'
        }
        
        print(f"\n📋 Test Case: {procedure_info['cpt_codes'][0]} (Knee replacement)")
        
        evaluation = self.evaluate_authorization(patient_info, procedure_info)
        self.display_results(evaluation)
        
        return evaluation


def main():
    """Main function"""
    
    system = InteractivePASystem()
    
    print("🏥 Welcome to the Interactive Prior Authorization System!")
    print("\nChoose an option:")
    print("1. Full interactive session")
    print("2. Quick test with sample data")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        evaluation = system.run_interactive_session()
    elif choice == '2':
        evaluation = system.run_quick_test()
    elif choice == '3':
        print("👋 Goodbye!")
        return
    else:
        print("❌ Invalid choice")
        return
    
    # Ask if they want to run another session
    if evaluation:
        while True:
            another = input("\n🔄 Run another authorization check? (y/n): ").strip().lower()
            if another in ['y', 'yes']:
                system.run_interactive_session()
            elif another in ['n', 'no']:
                break
            else:
                print("Please enter 'y' or 'n'")
    
    print("\n👋 Thank you for using the PA system!")


if __name__ == "__main__":
    main()
