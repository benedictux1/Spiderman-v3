#!/usr/bin/env python3
"""
Comprehensive migration verification script
"""

import sys
import os
import traceback
from datetime import datetime

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all critical imports work correctly"""
    try:
        print("Testing imports...")

        # Test database configuration
        from config.database import DatabaseConfig
        print("✓ Database configuration imported")

        # Test database manager
        from app.utils.database import DatabaseManager
        print("✓ Database manager imported")

        # Test models
        from models import Base, User, Contact, RawNote, SynthesizedEntry
        print("✓ Models imported")

        # Test new application structure
        from app import create_app
        print("✓ App factory imported")

        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        traceback.print_exc()
        return False

def test_database_configuration():
    """Test database configuration"""
    try:
        print("\nTesting database configuration...")

        from config.database import DatabaseConfig

        # Test URL generation
        url = DatabaseConfig.get_database_url()
        print(f"✓ Database URL: {url}")

        if not url.startswith('postgresql://'):
            print(f"✗ Expected PostgreSQL URL, got: {url}")
            return False

        # Test engine creation
        engine = DatabaseConfig.create_engine()
        print("✓ Engine created successfully")

        return True
    except Exception as e:
        print(f"✗ Database configuration failed: {e}")
        traceback.print_exc()
        return False

def test_database_connection():
    """Test actual database connection"""
    try:
        print("\nTesting database connection...")

        from app.utils.database import DatabaseManager
        from models import User

        db_manager = DatabaseManager()
        print("✓ Database manager initialized")

        # Test session creation
        with db_manager.get_session() as session:
            print("✓ Database session created")

            # Test basic query (this may take time on first run)
            user_count = session.query(User).count()
            print(f"✓ Database query successful - {user_count} users found")

        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        traceback.print_exc()
        return False

def test_json_fields():
    """Test that JSON fields work correctly with PostgreSQL"""
    try:
        print("\nTesting PostgreSQL JSON fields...")

        from app.utils.database import DatabaseManager
        from models import Contact, RawNote
        import json

        db_manager = DatabaseManager()

        with db_manager.get_session() as session:
            # Test creating a contact with JSON fields
            test_contact = Contact(
                user_id=1,  # Assuming user exists
                full_name="Test Contact",
                tier=2,
                telegram_metadata={"test": "data", "verified": True},
                custom_fields={"notes": "Test JSON field", "tags": ["test", "verification"]}
            )

            # Add to session but don't commit (just test the functionality)
            session.add(test_contact)
            session.flush()  # This will test JSON serialization

            print("✓ PostgreSQL JSON fields working correctly")

        return True
    except Exception as e:
        print(f"✗ JSON fields test failed: {e}")
        traceback.print_exc()
        return False

def test_app_creation():
    """Test that the new app structure works"""
    try:
        print("\nTesting application creation...")

        from app import create_app
        from config.settings import DevelopmentConfig

        # Create app instance
        app = create_app(DevelopmentConfig)
        print("✓ App created successfully")

        # Test app configuration
        if app.config.get('SQLALCHEMY_DATABASE_URI'):
            print("✓ Database configuration loaded")

        return True
    except Exception as e:
        print(f"✗ App creation failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all verification tests"""
    print("=" * 60)
    print("SQLite to PostgreSQL Migration Verification")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("Database Configuration", test_database_configuration),
        ("Database Connection", test_database_connection),
        ("JSON Fields", test_json_fields),
        ("App Creation", test_app_creation),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * 20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\n🎉 All tests passed! Migration verification successful.")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())