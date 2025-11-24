#!/usr/bin/env python3
"""
Schema validation script for pregnancy records.
Validates sample data against the pregnancy_schema.json schema.
"""

import json
import sys
from pathlib import Path
from jsonschema import validate, ValidationError, Draft7Validator

def load_schema():
    """Load the pregnancy schema from file."""
    schema_path = Path(__file__).parent / "pregnancy_schema.json"
    with open(schema_path, 'r') as f:
        return json.load(f)

def validate_sample_data():
    """Validate sample pregnancy records against the schema."""
    schema = load_schema()
    
    # Sample records to validate
    sample_records = [
        {
            "phone": "+2347012345678",
            "name": "Amina Diallo",
            "age": 28,
            "lmp_date": "2025-06-09",
            "edd": "2026-03-16",
            "location": "Dakar",
            "country": "Senegal",
            "risk_level": "low",
            "status": "active"
        },
        {
            "phone": "+1234567890",
            "name": "Sarah Johnson",
            "lmp_date": "2025-10-19",
            "edd": "2026-07-26",
            "location": "Lagos",
            "country": "Nigeria",
            "age": 25
        },
        {
            "phone": "+3456789012",
            "name": "Grace Mensah",
            "lmp_date": "2025-01-05",
            "edd": "2025-10-12",
            "location": "Accra",
            "country": "Ghana",
            "age": 32,
            "risk_level": "moderate",
            "medical_history": {
                "previous_pregnancies": 2,
                "chronic_conditions": ["hypertension"],
                "blood_type": "A+"
            }
        }
    ]
    
    print("="*70)
    print("  PREGNANCY SCHEMA VALIDATION")
    print("="*70)
    print()
    
    validator = Draft7Validator(schema)
    all_valid = True
    
    for i, record in enumerate(sample_records, 1):
        print(f"Validating Record {i}: {record.get('name', 'Unknown')}")
        print(f"  Phone: {record.get('phone')}")
        
        try:
            validate(instance=record, schema=schema)
            print(f"  ✅ VALID")
        except ValidationError as e:
            print(f"  ❌ INVALID")
            print(f"  Error: {e.message}")
            print(f"  Path: {' -> '.join(str(p) for p in e.path)}")
            all_valid = False
        
        print()
    
    # Validate schema itself
    print("Validating Schema Structure...")
    try:
        Draft7Validator.check_schema(schema)
        print("  ✅ Schema is valid JSON Schema Draft 7")
    except Exception as e:
        print(f"  ❌ Schema validation failed: {e}")
        all_valid = False
    
    print()
    print("="*70)
    
    if all_valid:
        print("✅ ALL VALIDATIONS PASSED")
        return 0
    else:
        print("❌ SOME VALIDATIONS FAILED")
        return 1

def test_invalid_data():
    """Test that invalid data is properly rejected."""
    schema = load_schema()
    
    print("\n" + "="*70)
    print("  TESTING INVALID DATA REJECTION")
    print("="*70)
    print()
    
    invalid_records = [
        {
            "name": "Missing Phone",
            "record": {
                "name": "Test User",
                "lmp_date": "2025-03-01"
            },
            "expected_error": "phone"
        },
        {
            "name": "Invalid LMP Date Format",
            "record": {
                "phone": "+1234567890",
                "name": "Test User",
                "lmp_date": "01-03-2025"
            },
            "expected_error": "format"
        },
        {
            "name": "Age Out of Range",
            "record": {
                "phone": "+1234567890",
                "name": "Test User",
                "lmp_date": "2025-03-01",
                "age": 5
            },
            "expected_error": "minimum"
        },
        {
            "name": "Invalid Risk Level",
            "record": {
                "phone": "+1234567890",
                "name": "Test User",
                "lmp_date": "2025-03-01",
                "risk_level": "very_high"
            },
            "expected_error": "enum"
        }
    ]
    
    all_rejected = True
    for test in invalid_records:
        print(f"Test: {test['name']}")
        try:
            validate(instance=test['record'], schema=schema)
            print(f"  ❌ FAILED - Record was accepted (should be rejected)")
            all_rejected = False
        except ValidationError as e:
            print(f"  ✅ PASSED - Correctly rejected")
            print(f"     Reason: {e.message[:60]}...")
        print()
    
    print("="*70)
    if all_rejected:
        print("✅ ALL INVALID DATA CORRECTLY REJECTED")
        return 0
    else:
        print("❌ SOME INVALID DATA WAS ACCEPTED")
        return 1

def print_schema_info():
    """Print information about the schema."""
    schema = load_schema()
    
    print("\n" + "="*70)
    print("  SCHEMA INFORMATION")
    print("="*70)
    print()
    print(f"Title: {schema.get('title')}")
    print(f"Description: {schema.get('description')}")
    print()
    print("Required Fields:")
    for field in schema.get('required', []):
        print(f"  • {field}")
    print()
    print("Optional Fields:")
    optional_fields = [k for k in schema.get('properties', {}).keys() 
                      if k not in schema.get('required', [])]
    for field in optional_fields:
        field_info = schema['properties'][field]
        field_type = field_info.get('type', 'unknown')
        print(f"  • {field} ({field_type})")
    print()
    print(f"Total Fields: {len(schema.get('properties', {}))}")
    print("="*70)

if __name__ == "__main__":
    print_schema_info()
    
    result1 = validate_sample_data()
    result2 = test_invalid_data()
    
    print("\n" + "="*70)
    print("  FINAL RESULT")
    print("="*70)
    
    if result1 == 0 and result2 == 0:
        print("\n🎉 ALL TESTS PASSED - SCHEMA IS VALID\n")
        sys.exit(0)
    else:
        print("\n⚠️  SOME TESTS FAILED\n")
        sys.exit(1)
