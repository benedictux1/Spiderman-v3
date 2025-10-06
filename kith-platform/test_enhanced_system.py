#!/usr/bin/env python3
"""
Test Enhanced Telegram System
Direct testing of the enhanced Telegram integration without Flask.
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

async def test_enhanced_telegram_system():
    """Test the complete enhanced Telegram system"""
    print("🚀 Testing Enhanced Telegram System")
    print("=" * 50)
    
    try:
        from app.services.enhanced_telegram_integration import EnhancedTelegramIntegration
        
        # Initialize integration
        user_id = "test_user_enhanced"
        integration = EnhancedTelegramIntegration(user_id)
        
        print(f"✅ Initialized EnhancedTelegramIntegration for user: {user_id}")
        
        # Test 1: Check session status
        print("\n🔍 Testing session status...")
        status = await integration.get_session_status()
        print(f"Session status: {status}")
        
        # Test 2: Connect to Telegram
        print("\n🔍 Testing Telegram connection...")
        connected = await integration.connect()
        if connected:
            print("✅ Successfully connected to Telegram!")
            
            # Test 3: Get session status after connection
            print("\n🔍 Testing session status after connection...")
            status = await integration.get_session_status()
            print(f"Connected status: {status.get('is_connected', False)}")
            print(f"Has session: {status.get('has_session', False)}")
            
            # Test 4: Get contacts
            print("\n🔍 Testing contacts retrieval...")
            contacts = await integration.get_contacts()
            print(f"✅ Retrieved {len(contacts)} contacts")
            
            if contacts:
                print("Sample contacts:")
                for i, contact in enumerate(contacts[:3]):  # Show first 3 contacts
                    print(f"  {i+1}. {contact.get('first_name', '')} {contact.get('last_name', '')} (@{contact.get('username', 'N/A')})")
            
            # Test 5: Get conversations (limited to avoid too much data)
            print("\n🔍 Testing conversations retrieval...")
            conversations = await integration.get_conversations(days_back=7)  # Last 7 days only
            print(f"✅ Retrieved {len(conversations)} conversations")
            
            if conversations:
                print("Sample conversations:")
                for i, conv in enumerate(conversations[:2]):  # Show first 2 conversations
                    print(f"  {i+1}. {conv.get('contact_name', 'Unknown')} - {len(conv.get('messages', []))} messages")
            
            # Test 6: Test specific contact sync
            if contacts:
                print("\n🔍 Testing specific contact sync...")
                first_contact = contacts[0]
                contact_identifier = first_contact.get('username') or first_contact.get('phone')
                if contact_identifier:
                    print(f"Syncing contact: {contact_identifier}")
                    conversation = await integration.sync_contact_history(contact_identifier, days_back=7)
                    if conversation:
                        print(f"✅ Synced {len(conversation.get('messages', []))} messages for {contact_identifier}")
                    else:
                        print(f"ℹ️ No recent messages found for {contact_identifier}")
            
            # Test 7: Disconnect
            print("\n🔍 Testing disconnection...")
            await integration.disconnect()
            print("✅ Successfully disconnected from Telegram")
            
            return True
        else:
            print("❌ Failed to connect to Telegram")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"Test error: {e}", exc_info=True)
        return False

async def test_session_persistence():
    """Test session persistence"""
    print("\n🔍 Testing session persistence...")
    
    try:
        from app.services.enhanced_telegram_integration import EnhancedTelegramIntegration
        
        user_id = "test_user_persistence"
        integration = EnhancedTelegramIntegration(user_id)
        
        # Connect and authenticate
        print("Connecting to Telegram...")
        connected = await integration.connect()
        
        if connected:
            print("✅ Connected successfully")
            
            # Get session info
            status = await integration.get_session_status()
            print(f"Session info: {status.get('session_info', {})}")
            
            # Disconnect
            await integration.disconnect()
            print("✅ Disconnected")
            
            # Test session restoration
            print("Testing session restoration...")
            integration2 = EnhancedTelegramIntegration(user_id)
            connected2 = await integration2.connect()
            
            if connected2:
                print("✅ Session restored successfully!")
                await integration2.disconnect()
                return True
            else:
                print("❌ Session restoration failed")
                return False
        else:
            print("❌ Initial connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Session persistence test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🧪 Enhanced Telegram System - Full Test Suite")
    print("=" * 60)
    
    # Test 1: Basic system test
    print("\n📋 Test 1: Enhanced Telegram System")
    test1_result = await test_enhanced_telegram_system()
    
    # Test 2: Session persistence
    print("\n📋 Test 2: Session Persistence")
    test2_result = await test_session_persistence()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    tests = [
        ("Enhanced Telegram System", test1_result),
        ("Session Persistence", test2_result)
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your enhanced Telegram system is fully functional!")
        print("\n📋 What you can do now:")
        print("1. Start the Flask app: python3 app.py")
        print("2. Open http://localhost:5001 in your browser")
        print("3. Go to Settings and use the Enhanced Telegram Integration")
        print("4. Sync your chat history with the new secure system")
    else:
        print(f"\n⚠️ {total - passed} tests failed. Check the logs above for details.")

if __name__ == "__main__":
    asyncio.run(main())
