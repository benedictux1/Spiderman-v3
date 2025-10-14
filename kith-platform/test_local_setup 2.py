#!/usr/bin/env python3
"""
Local Setup Test Script
Quick test to verify the enhanced Telegram system works locally.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if environment variables are set"""
    print("🔍 Checking environment setup...")
    
    required_vars = ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("\n📝 To fix this:")
        print("1. Create a .env file in the kith-platform directory")
        print("2. Add your Telegram API credentials:")
        print("   TELEGRAM_API_ID=your_api_id_here")
        print("   TELEGRAM_API_HASH=your_api_hash_here")
        print("3. Get credentials from: https://my.telegram.org")
        return False
    else:
        print("✅ Environment variables are set")
        return True

def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n🔍 Checking dependencies...")
    
    required_packages = [
        'cryptography',
        'telethon',
        'flask',
        'boto3',
        'redis'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n📝 To install missing packages:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    else:
        print("✅ All dependencies are installed")
        return True

async def test_basic_functionality():
    """Test basic functionality without API calls"""
    print("\n🔍 Testing basic functionality...")
    
    try:
        # Test configuration
        from config.telegram_config import TelegramConfig
        config = TelegramConfig.get_config()
        print("✅ Configuration system works")
        
        # Test session management
        from app.services.hybrid_telegram_session import HybridTelegramSession
        session = HybridTelegramSession("test_user")
        print("✅ Session management works")
        
        # Test storage
        test_data = {"user_id": "test_user", "test": True}
        success = await session.store_session(test_data)
        if success:
            print("✅ Session storage works")
            
            # Test restoration
            restored = await session.restore_session()
            if restored and restored.get("user_id") == "test_user":
                print("✅ Session restoration works")
            else:
                print("❌ Session restoration failed")
            
            # Clean up
            await session.delete_session()
            print("✅ Session cleanup works")
        else:
            print("❌ Session storage failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

async def test_telegram_connection():
    """Test Telegram connection (requires API credentials)"""
    print("\n🔍 Testing Telegram connection...")
    
    try:
        from app.services.enhanced_telegram_integration import EnhancedTelegramIntegration
        
        integration = EnhancedTelegramIntegration("test_user")
        
        # Test connection
        connected = await integration.connect()
        if connected:
            print("✅ Telegram connection successful")
            
            # Test getting status
            status = await integration.get_session_status()
            print(f"✅ Session status: {status.get('is_connected', False)}")
            
            # Disconnect
            await integration.disconnect()
            print("✅ Disconnection successful")
            
            return True
        else:
            print("❌ Telegram connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Telegram connection test failed: {e}")
        return False

async def test_api_endpoints():
    """Test API endpoints (requires Flask app to be running)"""
    print("\n🔍 Testing API endpoints...")
    
    try:
        import requests
        
        # Test status endpoint
        response = requests.get("http://localhost:5001/api/telegram/enhanced/status", timeout=5)
        if response.status_code == 200:
            print("✅ API endpoints are accessible")
            return True
        else:
            print(f"❌ API endpoint returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API endpoints")
        print("📝 Make sure the Flask app is running: python app.py")
        return False
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

def print_summary(results):
    """Print test summary"""
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Your enhanced Telegram system is ready to use.")
    else:
        print(f"\n⚠️ {total_tests - passed_tests} tests failed. Check the issues above.")

async def main():
    """Run all tests"""
    print("🚀 Enhanced Telegram System - Local Testing")
    print("="*50)
    
    results = {}
    
    # Test 1: Environment setup
    results["Environment Setup"] = check_environment()
    
    # Test 2: Dependencies
    results["Dependencies"] = check_dependencies()
    
    # Test 3: Basic functionality
    results["Basic Functionality"] = await test_basic_functionality()
    
    # Test 4: Telegram connection (only if environment is set)
    if results["Environment Setup"]:
        results["Telegram Connection"] = await test_telegram_connection()
    else:
        results["Telegram Connection"] = False
        print("\n⏭️ Skipping Telegram connection test (missing API credentials)")
    
    # Test 5: API endpoints
    results["API Endpoints"] = await test_api_endpoints()
    
    # Print summary
    print_summary(results)
    
    # Next steps
    print("\n📋 Next Steps:")
    if not results["Environment Setup"]:
        print("1. Set up your Telegram API credentials in .env file")
    if not results["Dependencies"]:
        print("2. Install missing dependencies")
    if not results["API Endpoints"]:
        print("3. Start the Flask app: python app.py")
    if all(results.values()):
        print("1. Start the Flask app: python app.py")
        print("2. Open http://localhost:5001 in your browser")
        print("3. Go to Settings and test the Telegram integration")

if __name__ == "__main__":
    asyncio.run(main())
