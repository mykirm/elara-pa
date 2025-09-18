#!/usr/bin/env python3
"""
Manual Testing Script for Prior Authorization System
Run this script to test various CPT codes and scenarios
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional

# Configuration
BASE_URL = "http://localhost:8000"
PAYER = "UnitedHealthcare"

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")

def print_test(test_name):
    print(f"\n{Colors.OKCYAN}▶ Testing: {test_name}{Colors.ENDC}")

def print_result(auth_required, confidence, reason=""):
    if auth_required == "REQUIRED" or auth_required == True:
        color = Colors.FAIL
        symbol = "🔴"
    elif auth_required == "NOT_REQUIRED" or auth_required == False:
        color = Colors.OKGREEN
        symbol = "🟢"
    else:
        color = Colors.WARNING
        symbol = "🟡"
    
    print(f"  {symbol} Authorization: {color}{auth_required}{Colors.ENDC}")
    print(f"  📊 Confidence: {confidence}")
    if reason:
        print(f"  💡 Reason: {reason}")

def test_basic_authorization(cpt_codes: List[str], icd_codes: List[str] = None, 
                            patient_age: int = 45, patient_state: str = "CA",
                            place_of_service: str = None):
    """Test basic authorization endpoint"""
    
    payload = {
        "cpt_codes": cpt_codes,
        "payer": PAYER,
        "patient_age": patient_age,
        "patient_state": patient_state
    }
    
    if icd_codes:
        payload["icd_codes"] = icd_codes
    
    try:
        response = requests.post(f"{BASE_URL}/authorization/evaluate", json=payload)
        if response.status_code == 200:
            data = response.json()
            auth_req = data.get("requires_authorization", "UNKNOWN")
            confidence = data.get("confidence_score", 0)
            reasoning = data.get("reasoning_path", [])
            
            print_result(auth_req, confidence)
            
            if data.get("applicable_rules"):
                print(f"  📋 Rules found: {len(data['applicable_rules'])}")
                for rule in data['applicable_rules'][:2]:  # Show first 2 rules
                    service = rule.get('service', 'N/A')[:50]
                    print(f"     - {service}...")
            
            return data
        else:
            print(f"  {Colors.FAIL}❌ Error: Status {response.status_code}{Colors.ENDC}")
            return None
    except Exception as e:
        print(f"  {Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
        return None

def test_smart_authorization(cpt_codes: List[str], icd_codes: List[str] = None,
                           patient_age: int = 45, patient_state: str = "CA",
                           place_of_service: str = "22"):
    """Test smart authorization endpoint"""
    
    payload = {
        "cpt_codes": cpt_codes,
        "payer": PAYER,
        "patient_age": patient_age,
        "patient_state": patient_state,
        "place_of_service": place_of_service
    }
    
    if icd_codes:
        payload["icd_codes"] = icd_codes
    
    try:
        response = requests.post(f"{BASE_URL}/authorization/evaluate-smart", json=payload)
        if response.status_code == 200:
            data = response.json()
            auth_req = data.get("requires_authorization", "UNKNOWN")
            confidence = data.get("confidence_score", 0)
            reason = data.get("primary_reason", "")
            
            print_result(auth_req, confidence, reason)
            
            context = data.get("context_provided", {})
            if context:
                print(f"  🎯 Context evaluated: Age={context.get('patient_age')}, "
                      f"POS={context.get('place_of_service')}, State={context.get('state')}")
            
            return data
        else:
            print(f"  {Colors.FAIL}❌ Error: Status {response.status_code}{Colors.ENDC}")
            return None
    except Exception as e:
        print(f"  {Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
        return None

def check_system_status():
    """Check if the system is running and get capabilities"""
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print(f"{Colors.OKGREEN}✅ System Online{Colors.ENDC}")
            print(f"  📚 Rules loaded: {data.get('rules_loaded', 0)}")
            print(f"  🔧 Parser mode: {data.get('parser_mode', 'Unknown')}")
            
            caps = data.get('capabilities', {})
            if caps.get('enhanced_evaluation_enabled'):
                print(f"  🚀 Enhanced evaluation: Enabled")
            
            return True
        else:
            print(f"{Colors.FAIL}❌ System not responding{Colors.ENDC}")
            return False
    except:
        print(f"{Colors.FAIL}❌ Cannot connect to {BASE_URL}{Colors.ENDC}")
        return False

def run_test_suite():
    """Run comprehensive test suite"""
    
    print_header("PRIOR AUTHORIZATION SYSTEM - MANUAL TEST SUITE")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check system status
    print_test("System Status")
    if not check_system_status():
        print(f"\n{Colors.FAIL}System is not running. Please start the server first.{Colors.ENDC}")
        return
    
    # Test cases
    test_cases = [
        {
            "name": "CPT 77014 - Radiation Therapy Setup",
            "cpt_codes": ["77014"],
            "icd_codes": None,
            "description": "Testing code that appears in category but not as direct CPT"
        },
        {
            "name": "CPT G6017 - IGRT (Related to 77014)",
            "cpt_codes": ["G6017"],
            "icd_codes": None,
            "description": "Testing actual CPT code from 77014 category"
        },
        {
            "name": "CPT 77401 with M16.9 - Radiation with Osteoarthritis",
            "cpt_codes": ["77401"],
            "icd_codes": ["M16.9"],
            "description": "Should NOT require auth (diagnosis not in D05 range)"
        },
        {
            "name": "CPT 77401 with D05.10 - Radiation with Carcinoma in situ",
            "cpt_codes": ["77401"],
            "icd_codes": ["D05.10"],
            "description": "Should require auth (diagnosis in D05 range)"
        },
        {
            "name": "CPT 0071T - MR-guided focused ultrasound",
            "cpt_codes": ["0071T"],
            "icd_codes": None,
            "description": "Code exists in source but may not be extracted"
        },
        {
            "name": "CPT 29826 - Arthroscopy shoulder",
            "cpt_codes": ["29826"],
            "icd_codes": None,
            "description": "Common arthroscopy code"
        },
        {
            "name": "CPT 43644 - Bariatric surgery",
            "cpt_codes": ["43644"],
            "icd_codes": None,
            "description": "Bariatric procedure"
        },
        {
            "name": "Multiple CPT codes - 70450, 70460, 70470",
            "cpt_codes": ["70450", "70460", "70470"],
            "icd_codes": None,
            "description": "Multiple CT scan codes"
        },
        {
            "name": "CPT 33776 - Pediatric vs Adult",
            "cpt_codes": ["33776"],
            "icd_codes": None,
            "patient_age": 10,
            "description": "Testing age-based rules (pediatric)"
        },
        {
            "name": "CPT 33776 - Adult Patient",
            "cpt_codes": ["33776"],
            "icd_codes": None,
            "patient_age": 45,
            "description": "Testing age-based rules (adult)"
        }
    ]
    
    # Run basic authorization tests
    print_header("BASIC AUTHORIZATION TESTS")
    
    for test in test_cases:
        print_test(test["name"])
        if test.get("description"):
            print(f"  📝 {test['description']}")
        
        result = test_basic_authorization(
            cpt_codes=test["cpt_codes"],
            icd_codes=test.get("icd_codes"),
            patient_age=test.get("patient_age", 45),
            patient_state=test.get("patient_state", "CA")
        )
    
    # Run smart authorization tests for select cases
    print_header("SMART AUTHORIZATION TESTS (With Context)")
    
    smart_tests = [
        {
            "name": "Office vs Hospital - CPT 77401",
            "cpt_codes": ["77401"],
            "place_of_service": "11",  # Office
            "description": "Testing place of service impact"
        },
        {
            "name": "Outpatient Hospital - CPT 77401",
            "cpt_codes": ["77401"],
            "place_of_service": "22",  # Outpatient Hospital
            "description": "Testing different place of service"
        },
        {
            "name": "Texas Exception - CPT 29826",
            "cpt_codes": ["29826"],
            "patient_state": "TX",
            "description": "Testing state-based exceptions"
        }
    ]
    
    for test in smart_tests:
        print_test(test["name"])
        if test.get("description"):
            print(f"  📝 {test['description']}")
        
        result = test_smart_authorization(
            cpt_codes=test["cpt_codes"],
            icd_codes=test.get("icd_codes"),
            patient_age=test.get("patient_age", 45),
            patient_state=test.get("patient_state", "CA"),
            place_of_service=test.get("place_of_service", "22")
        )
    
    print_header("TEST SUITE COMPLETED")

def interactive_test():
    """Interactive testing mode"""
    print_header("INTERACTIVE TEST MODE")
    print("Enter CPT codes to test (or 'quit' to exit)")
    
    while True:
        print(f"\n{Colors.OKCYAN}Enter CPT code(s) separated by comma:{Colors.ENDC} ", end="")
        user_input = input().strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
        
        if not user_input:
            continue
        
        cpt_codes = [code.strip() for code in user_input.split(',')]
        
        # Optional ICD codes
        print(f"{Colors.OKCYAN}Enter ICD code(s) separated by comma (or press Enter to skip):{Colors.ENDC} ", end="")
        icd_input = input().strip()
        icd_codes = [code.strip() for code in icd_input.split(',')] if icd_input else None
        
        # Test the codes
        print_test(f"Testing CPT: {', '.join(cpt_codes)}")
        test_basic_authorization(cpt_codes, icd_codes)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_test()
    else:
        run_test_suite()
        print(f"\n{Colors.OKCYAN}Tip: Run with 'python manual_test_auth.py interactive' for interactive mode{Colors.ENDC}")