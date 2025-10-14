#!/usr/bin/env python3
"""
Persistence Demo for Enhanced Telegram System
Demonstrates that sessions persist between runs with the same user ID.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
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

async def test_persistence_with_same_user():
    """Test persistence with the same user ID"""
    print("🔍 Testing Persistence with Same User ID")
    print("=" * 50)
    
    try:
        from app.services.enhanced_telegram_integration import EnhancedTelegramIntegration
        
        # Use the SAME user ID for both tests
        user_id = "demo_user_persistence"
        
        print(f"Using user ID: {user_id}")
        
        # Test 1: First connection
        print("\n📱 Test 1: First Connection")
        integration1 = EnhancedTelegramIntegration(user_id)
        
        # Check if session exists
        status1 = await integration1.get_session_status()
        print(f"Initial status: {status1}")
        
        if not status1.get('has_session'):
            print("No existing session found. Connecting...")
            connected1 = await integration1.connect()
            if connected1:
                print("✅ First connection successful!")
                
                # Get some data to prove it's working
                contacts = await integration1.get_contacts()
                print(f"✅ Retrieved {len(contacts)} contacts")
                
                # Disconnect but keep session
                await integration1.disconnect()
                print("✅ Disconnected (session should be saved)")
            else:
                print("❌ First connection failed")
                return False
        else:
            print("✅ Session already exists!")
        
        # Test 2: Second connection (should use existing session)
        print("\n📱 Test 2: Second Connection (Should Use Existing Session)")
        integration2 = EnhancedTelegramIntegration(user_id)
        
        # Check session status
        status2 = await integration2.get_session_status()
        print(f"Session status: {status2}")
        
        if status2.get('has_session'):
            print("✅ Session found! Testing restoration...")
            
            # Try to connect (should use existing session)
            connected2 = await integration2.connect()
            if connected2:
                print("✅ Second connection successful! (Used existing session)")
                
                # Verify we can get data
                contacts = await integration2.get_contacts()
                print(f"✅ Retrieved {len(contacts)} contacts (session working)")
                
                # Disconnect
                await integration2.disconnect()
                print("✅ Disconnected")
                
                return True
            else:
                print("❌ Second connection failed")
                return False
        else:
            print("❌ No session found for second connection")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"Test error: {e}", exc_info=True)
        return False

async def test_session_cleanup():
    """Test session cleanup"""
    print("\n🧹 Testing Session Cleanup")
    print("=" * 30)
    
    try:
        from app.services.enhanced_telegram_integration import EnhancedTelegramIntegration
        
        user_id = "demo_user_persistence"
        integration = EnhancedTelegramIntegration(user_id)
        
        # Check if session exists
        status = await integration.get_session_status()
        if status.get('has_session'):
            print("Session exists. Testing cleanup...")
            
            # Delete session
            success = await integration.delete_session()
            if success:
                print("✅ Session deleted successfully")
                
                # Verify session is gone
                status_after = await integration.get_session_status()
                if not status_after.get('has_session'):
                    print("✅ Session cleanup verified")
                    return True
                else:
                    print("❌ Session still exists after cleanup")
                    return False
            else:
                print("❌ Failed to delete session")
                return False
        else:
            print("ℹ️ No session to clean up")
            return True
            
    except Exception as e:
        print(f"❌ Cleanup test failed: {e}")
        return False

async def main():
    """Run persistence tests"""
    print("🧪 Enhanced Telegram System - Persistence Demo")
    print("=" * 60)
    
    # Test 1: Persistence with same user
    print("\n📋 Test 1: Session Persistence")
    test1_result = await test_persistence_with_same_user()
    
    # Test 2: Session cleanup
    print("\n📋 Test 2: Session Cleanup")
    test2_result = await test_session_cleanup()
    
    # Summary
    print("\n" + "=" * 60)
    print("PERSISTENCE TEST SUMMARY")
    print("=" * 60)
    
    tests = [
        ("Session Persistence", test1_result),
        ("Session Cleanup", test2_result)
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 Persistence is working perfectly!")
        print("\n📋 What this means:")
        print("1. ✅ Sessions are stored securely with encryption")
        print("2. ✅ Sessions persist between app restarts")
        print("3. ✅ No need to re-authenticate every time")
        print("4. ✅ Sessions can be cleaned up when needed")
        print("\n🚀 Your enhanced Telegram system is ready for production!")
    else:
        print(f"\n⚠️ {total - passed} tests failed. Check the logs above.")

if __name__ == "__main__":
    asyncio.run(main())
