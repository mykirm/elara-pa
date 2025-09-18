#!/usr/bin/env python3
"""
Demo Interactive PA System
==========================

Demonstrates the interactive system with a sample session.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from interactive_pa_system import InteractivePASystem


def demo_interactive_session():
    """Demo of interactive PA session"""
    
    system = InteractivePASystem()
    
    print("🎬 DEMO: Interactive Prior Authorization Session")
    print("=" * 60)
    
    # Demo patient info
    patient_info = {
        'patient_id': 'DEMO_001',
        'age': 55,
        'state': 'CA',
        'payer': 'UnitedHealthcare',
        'plan_type': 'PPO'
    }
    
    # Demo procedure info - Hip replacement
    procedure_info = {
        'cpt_codes': ['27130'],  # Hip replacement 
        'icd_codes': ['M16.9'],  # Hip osteoarthritis
        'place_of_service': '22',
        'place_of_service_desc': 'Outpatient Hospital',
        'provider_specialty': 'Orthopedic Surgery'
    }
    
    print("\n📋 Demo Patient Information:")
    print(f"  • Patient ID: {patient_info['patient_id']}")
    print(f"  • Age: {patient_info['age']}")
    print(f"  • State: {patient_info['state']}")
    print(f"  • Insurance: {patient_info['payer']} {patient_info['plan_type']}")
    
    print("\n🏥 Demo Procedure Information:")
    print(f"  • CPT Codes: {', '.join(procedure_info['cpt_codes'])}")
    print(f"  • Diagnosis: {', '.join(procedure_info['icd_codes'])}")
    print(f"  • Place of Service: {procedure_info['place_of_service_desc']}")
    print(f"  • Provider Specialty: {procedure_info['provider_specialty']}")
    
    # Evaluate authorization
    evaluation = system.evaluate_authorization(patient_info, procedure_info)
    
    # Display full results
    system.display_results(evaluation)
    
    return evaluation


def show_system_capabilities():
    """Show what the interactive system can do"""
    
    print("\n🛠️  INTERACTIVE PA SYSTEM CAPABILITIES")
    print("=" * 50)
    
    capabilities = [
        "📋 Patient Information Collection",
        "   • Demographics (age, state)",
        "   • Insurance details (payer, plan type)",
        "",
        "🏥 Procedure Information Collection", 
        "   • CPT/HCPCS codes (multiple supported)",
        "   • ICD-10 diagnosis codes",
        "   • Place of service selection",
        "   • Provider specialty",
        "",
        "🔍 Rule Matching & Evaluation",
        "   • CPT code matching against 166 loaded rules",
        "   • State exclusion checking",
        "   • Age restriction validation",
        "   • Payer-specific rule application",
        "",
        "🎯 Authorization Decision",
        "   • REQUIRED / NOT_REQUIRED / CONDITIONAL",
        "   • Detailed reasoning provided",
        "   • Specific rule citations",
        "",
        "💡 Actionable Recommendations",
        "   • Next steps for providers",
        "   • Required documentation",
        "   • Contact information",
        "",
        "💾 Session Management",
        "   • Save evaluation results",
        "   • Audit trail for decisions",
        "   • JSON export capability"
    ]
    
    for item in capabilities:
        print(item)
    
    print("\n🚀 Usage Examples:")
    print("   python interactive_pa_system.py    # Full interactive mode")
    print("   python quick_pa_test.py           # Quick test scenarios")
    print("   python demo_interactive_pa.py     # This demo")


if __name__ == "__main__":
    demo_interactive_session()
    show_system_capabilities()
    
    print("\n" + "=" * 60)
    print("✨ Ready to use the Interactive PA System!")
    print("=" * 60)
