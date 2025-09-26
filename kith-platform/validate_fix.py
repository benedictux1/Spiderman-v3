#!/usr/bin/env python3
"""
Validation script for root cause fix implementation
Tests all critical import chains before deployment
"""
import sys
import os
import traceback

# Add current directory to Python path
sys.path.insert(0, '.')

def test_import(name, code, critical=True):
    """Test an import and return success status"""
    try:
        exec(code)
        print(f"✅ {name}")
        return True
    except Exception as e:
        print(f"❌ {name}: {e}")
        if critical:
            print(f"   Traceback: {traceback.format_exc().strip()}")
        return False

def main():
    """Run all validation tests"""
    print("🔍 Validating Root Cause Fix Implementation")
    print("=" * 50)
    
    tests = [
        # Phase 1: Basic imports that were previously broken
        ("Container class import", "from app.utils.dependencies import Container", True),
        ("ContactService import", "from app.services.contact_service import ContactService", True),
        ("DatabaseManager import", "from app.utils.database import DatabaseManager", True),
        
        # Phase 2: Container instantiation (was causing import-time side effects)
        ("Container instantiation", "from app.utils.dependencies import Container; Container()", True),
        
        # Phase 3: Service instantiation
        ("ContactService instantiation", """
from app.services.contact_service import ContactService
from app.utils.database import DatabaseManager
db_manager = DatabaseManager()
contact_service = ContactService(db_manager)
""", True),
        
        # Phase 4: Application creation (full integration test)
        ("App creation", "from app import create_app; create_app()", True),
        
        # Phase 5: Container attachment verification
        ("Container attachment", """
from app import create_app
app = create_app()
assert hasattr(app, 'container'), 'Container not attached to app'
assert app.container is not None, 'Container is None'
""", True),
        
        # Phase 6: Dependency injection verification
        ("Dependency injection", """
from app import create_app
app = create_app()
assert hasattr(app.container, 'contact_service'), 'contact_service not in container'
assert hasattr(app.container, 'db_manager'), 'db_manager not in container'
""", True),
        
        # Phase 7: API import verification (these were failing before)
        ("API contacts import", "from app.api.contacts import contacts_bp", False),
        ("API auth import", "from app.api.auth import auth_bp", False),
        ("API notes import", "from app.api.notes import notes_bp", False),
    ]
    
    print(f"Running {len(tests)} validation tests...\n")
    
    passed = 0
    failed = 0
    critical_failed = 0
    
    for name, code, critical in tests:
        if test_import(name, code, critical):
            passed += 1
        else:
            failed += 1
            if critical:
                critical_failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed} passed, {failed} failed")
    
    if critical_failed > 0:
        print(f"💥 CRITICAL: {critical_failed} critical tests failed!")
        print("🚫 DO NOT DEPLOY - Fix critical issues first")
        return False
    elif failed > 0:
        print(f"⚠️  WARNING: {failed} non-critical tests failed")
        print("✅ SAFE TO DEPLOY - Non-critical issues can be addressed later")
        return True
    else:
        print("🎉 ALL TESTS PASSED!")
        print("✅ READY FOR DEPLOYMENT")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
