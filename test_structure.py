#!/usr/bin/env python3
"""
Simple test to verify the application structure and imports
"""

import sys
import os
import importlib.util

def test_import(module_path, name):
    """Test if a module can be imported"""
    try:
        spec = importlib.util.spec_from_file_location(name, module_path)
        if spec is None:
            return False, f"Could not create spec for {name}"
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return True, f"Successfully imported {name}"
    except Exception as e:
        return False, f"Failed to import {name}: {str(e)}"

def main():
    """Run basic structure tests"""
    print("Testing CarScraping Application Structure")
    print("=" * 50)
    
    # Test core modules
    tests = [
        ("app/core/config.py", "app.core.config"),
        ("app/models/models.py", "app.models.models"), 
        ("app/models/schemas.py", "app.models.schemas"),
    ]
    
    all_passed = True
    
    for module_path, module_name in tests:
        if os.path.exists(module_path):
            success, message = test_import(module_path, module_name)
            print(f"{'✓' if success else '✗'} {message}")
            if not success:
                all_passed = False
        else:
            print(f"✗ File not found: {module_path}")
            all_passed = False
    
    # Test file structure
    print("\nChecking File Structure:")
    required_files = [
        "app/main.py",
        "app/templates/base.html",
        "app/templates/dashboard.html",
        "app/static/css/style.css",
        "app/static/js/app.js",
        "docker-compose.yml",
        "Dockerfile",
        "requirements.txt"
    ]
    
    for file_path in required_files:
        exists = os.path.exists(file_path)
        print(f"{'✓' if exists else '✗'} {file_path}")
        if not exists:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All basic structure tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())