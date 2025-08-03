#!/usr/bin/env python3
"""
Verification script to check that the Cambridge AI Tutor structure is properly set up
"""
import os
import sys

def check_directory_structure():
    """Check that all required directories and files exist"""
    base_path = os.path.dirname(__file__)
    
    required_structure = {
        'directories': [
            'services',
            'models', 
            'repositories',
            'tests'
        ],
        'files': [
            '__init__.py',
            'api.py',
            'services/__init__.py',
            'services/tutor_service.py',
            'services/content_service.py',
            'models/__init__.py',
            'models/user_models.py',
            'models/curriculum_models.py',
            'repositories/__init__.py',
            'repositories/base_repository.py',
            'tests/__init__.py',
            'tests/test_structure.py'
        ]
    }
    
    print("Checking Cambridge AI Tutor directory structure...")
    
    # Check directories
    for directory in required_structure['directories']:
        dir_path = os.path.join(base_path, directory)
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            print(f"✓ Directory: {directory}")
        else:
            print(f"✗ Missing directory: {directory}")
            return False
    
    # Check files
    for file_path in required_structure['files']:
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            print(f"✓ File: {file_path}")
        else:
            print(f"✗ Missing file: {file_path}")
            return False
    
    return True

def check_database_migration():
    """Check that the database migration exists"""
    migration_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'supabase', 
        'migrations', 
        '20250802223408_cambridge_ai_tutor_schema.sql'
    )
    
    if os.path.exists(migration_path):
        print("✓ Database migration: 20250802223408_cambridge_ai_tutor_schema.sql")
        return True
    else:
        print("✗ Missing database migration")
        return False

def check_api_integration():
    """Check that the API is integrated into the main API file"""
    api_path = os.path.join(os.path.dirname(__file__), '..', 'api.py')
    
    if not os.path.exists(api_path):
        print("✗ Main API file not found")
        return False
    
    with open(api_path, 'r') as f:
        content = f.read()
        
    if 'from tutor import api as tutor_api' in content:
        print("✓ Tutor API import in main API")
    else:
        print("✗ Tutor API not imported in main API")
        return False
        
    if 'tutor_api.router' in content:
        print("✓ Tutor API router included")
    else:
        print("✗ Tutor API router not included")
        return False
        
    if 'tutor_api.initialize(db)' in content:
        print("✓ Tutor API initialization")
        return True
    else:
        print("✗ Tutor API not initialized")
        return False

def main():
    """Main verification function"""
    print("=" * 60)
    print("Cambridge AI Tutor Structure Verification")
    print("=" * 60)
    
    checks = [
        ("Directory Structure", check_directory_structure),
        ("Database Migration", check_database_migration),
        ("API Integration", check_api_integration)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        print("-" * 30)
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All checks passed! Cambridge AI Tutor structure is properly set up.")
        sys.exit(0)
    else:
        print("✗ Some checks failed. Please review the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()