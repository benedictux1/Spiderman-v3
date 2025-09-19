#!/usr/bin/env python3
"""
Simple database configuration test
"""

import sys
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_db_config():
    """Test database configuration without making connections"""
    try:
        from config.database import DatabaseConfig

        # Test database URL configuration
        db_url = DatabaseConfig.get_database_url()
        print(f"Database URL: {db_url}")

        # Check if it's PostgreSQL
        if db_url.startswith('postgresql://'):
            print("✓ PostgreSQL URL detected")
        else:
            print(f"✗ Non-PostgreSQL URL detected: {db_url}")

        # Check environment variables
        print(f"DATABASE_URL env var: {os.getenv('DATABASE_URL', 'NOT SET')}")
        print(f"DEV_DATABASE_URL env var: {os.getenv('DEV_DATABASE_URL', 'NOT SET')}")

        return True

    except Exception as e:
        print(f"Configuration test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_db_config()
    sys.exit(0 if success else 1)