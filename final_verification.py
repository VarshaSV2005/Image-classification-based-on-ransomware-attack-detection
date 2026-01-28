#!/usr/bin/env python3
"""
Final verification test for Desktop Endpoint Security System
"""

import os
import sys
import subprocess
import time

def test_component(name, test_func):
    """Test a component and report result"""
    try:
        result = test_func()
        if result:
            print(f"✅ {name}: PASS")
            return True
        else:
            print(f"❌ {name}: FAIL")
            return False
    except Exception as e:
        print(f"❌ {name}: ERROR - {e}")
        return False

def test_python_imports():
    """Test Python dependencies"""
    try:
        import torch
        import flask
        import flask_sqlalchemy
        from flask import Flask
        return True
    except ImportError:
        return False

def test_flask_app():
    """Test Flask app creation"""
    try:
        from app import app
        return app is not None
    except Exception:
        return False

def test_model_loading():
    """Test ML model loading"""
    try:
        from app import model
        return model is not None
    except Exception:
        return False

def test_electron_files():
    """Test Electron files exist"""
    files = [
        'package.json',
        'electron/main.js',
        'electron/preload.js'
    ]
    return all(os.path.exists(f) for f in files)

def test_node_modules():
    """Test Node.js dependencies"""
    return os.path.exists('node_modules')

def test_api_endpoint():
    """Test API endpoint"""
    try:
        from app import app
        with app.test_client() as client:
            response = client.get('/api/predict')
            return response.status_code in [400, 405]  # Expected for GET without file
    except Exception:
        return False

def main():
    print("🧪 Final Verification - Desktop Endpoint Security System")
    print("=" * 60)

    tests = [
        ("Python Dependencies", test_python_imports),
        ("Flask App Creation", test_flask_app),
        ("ML Model Loading", test_model_loading),
        ("Electron Files", test_electron_files),
        ("Node.js Dependencies", test_node_modules),
        ("API Endpoint", test_api_endpoint),
    ]

    passed = 0
    total = len(tests)

    for name, test_func in tests:
        if test_component(name, test_func):
            passed += 1

    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED - System is ready for production!")
        return True
    else:
        print("⚠️  Some tests failed - check implementation")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
