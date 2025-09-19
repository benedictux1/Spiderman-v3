#!/usr/bin/env python3
"""
Test PostgreSQL connection directly
"""

import sys
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_postgres_connection():
    """Test direct PostgreSQL connection"""
    try:
        import psycopg2

        # Connection parameters
        conn_params = {
            'host': 'localhost',
            'port': 5432,
            'database': 'kith_dev',
            'user': 'postgres',
            'password': 'postgres'
        }

        print("Testing PostgreSQL connection...")
        print(f"Host: {conn_params['host']}")
        print(f"Port: {conn_params['port']}")
        print(f"Database: {conn_params['database']}")
        print(f"User: {conn_params['user']}")

        # Try to connect
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()

        # Test a simple query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✓ PostgreSQL version: {version[0]}")

        # Check if our database exists
        cursor.execute("SELECT datname FROM pg_database WHERE datname = %s;", (conn_params['database'],))
        db_exists = cursor.fetchone()

        if db_exists:
            print(f"✓ Database '{conn_params['database']}' exists")
        else:
            print(f"✗ Database '{conn_params['database']}' does not exist")

        cursor.close()
        conn.close()

        return True

    except ImportError:
        print("✗ psycopg2 not installed")
        return False
    except Exception as e:
        print(f"✗ PostgreSQL connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_postgres_connection()
    sys.exit(0 if success else 1)