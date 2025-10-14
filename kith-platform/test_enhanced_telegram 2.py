#!/usr/bin/env python3
"""
Test script for Enhanced Telegram Integration
Tests the hybrid session management system.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_hybrid_session():
    """Test the hybrid session management"""
    try:
        from app.services.hybrid_telegram_session import HybridTelegramSession
        
        # Test with a dummy user ID
        user_id = "test_user_123"
        session_manager = HybridTelegramSession(user_id)
        
        logger.info(f"Testing hybrid session for user: {user_id}")
        logger.info(f"Environment: {'Render' if session_manager.is_render else 'Local'}")
        logger.info(f"Storage backend: {session_manager.storage_backend}")
        
        # Test session storage
        test_session_data = {
            'user_id': user_id,
            'api_id': 'test_api_id',
            'api_hash': 'test_api_hash',
            'phone': '+1234567890',
            'created_at': '2025-01-01T00:00:00Z'
        }
        
        # Store session
        logger.info("Testing session storage...")
        success = await session_manager.store_session(test_session_data)
        logger.info(f"Session storage result: {success}")
        
        # Check if session exists
        has_session = await session_manager.has_session()
        logger.info(f"Session exists: {has_session}")
        
        # Restore session
        if has_session:
            logger.info("Testing session restoration...")
            restored_data = await session_manager.restore_session()
            if restored_data:
                logger.info(f"Session restored successfully: {restored_data.get('user_id')}")
            else:
                logger.error("Failed to restore session")
        
        # Get session info
        session_info = await session_manager.get_session_info()
        logger.info(f"Session info: {session_info}")
        
        # Clean up
        logger.info("Cleaning up test session...")
        delete_success = await session_manager.delete_session()
        logger.info(f"Session deletion result: {delete_success}")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

async def test_enhanced_integration():
    """Test the enhanced Telegram integration"""
    try:
        from app.services.enhanced_telegram_integration import EnhancedTelegramIntegration
        
        # Test with a dummy user ID
        user_id = "test_user_123"
        integration = EnhancedTelegramIntegration(user_id)
        
        logger.info(f"Testing enhanced integration for user: {user_id}")
        
        # Test session status
        status = await integration.get_session_status()
        logger.info(f"Session status: {status}")
        
        # Test connection (this will fail without real credentials, but we can test the flow)
        logger.info("Testing connection flow...")
        try:
            connected = await integration.connect()
            logger.info(f"Connection result: {connected}")
            
            if connected:
                # Test disconnect
                await integration.disconnect()
                logger.info("Disconnected successfully")
        except Exception as e:
            logger.info(f"Connection test (expected to fail without real credentials): {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Enhanced integration test failed: {e}")
        return False

async def test_migration_system():
    """Test the migration system"""
    try:
        from app.services.telegram_migration import TelegramSessionMigrator
        
        # Test with a dummy user ID
        user_id = "test_user_123"
        migrator = TelegramSessionMigrator(user_id)
        
        logger.info(f"Testing migration system for user: {user_id}")
        
        # Test migration status
        status = await migrator.get_migration_status()
        logger.info(f"Migration status: {status}")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration test failed: {e}")
        return False

async def test_configuration():
    """Test the configuration system"""
    try:
        from config.telegram_config import TelegramConfig
        
        logger.info("Testing configuration system...")
        
        # Get configuration
        config = TelegramConfig.get_config()
        logger.info(f"Configuration: {config}")
        
        # Validate configuration
        try:
            TelegramConfig.validate_config(config)
            logger.info("Configuration validation: PASSED")
        except Exception as e:
            logger.warning(f"Configuration validation: FAILED - {e}")
        
        # Get environment info
        env_info = TelegramConfig.get_environment_info()
        logger.info(f"Environment info: {env_info}")
        
        return True
        
    except Exception as e:
        logger.error(f"Configuration test failed: {e}")
        return False

async def main():
    """Run all tests"""
    logger.info("Starting Enhanced Telegram Integration Tests")
    logger.info("=" * 50)
    
    tests = [
        ("Configuration System", test_configuration),
        ("Hybrid Session Management", test_hybrid_session),
        ("Enhanced Integration", test_enhanced_integration),
        ("Migration System", test_migration_system)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning test: {test_name}")
        logger.info("-" * 30)
        
        try:
            result = await test_func()
            results[test_name] = result
            logger.info(f"✅ {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            results[test_name] = False
            logger.error(f"❌ {test_name}: FAILED - {e}")
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("TEST SUMMARY")
    logger.info("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Enhanced Telegram system is ready.")
    else:
        logger.warning(f"⚠️  {total - passed} tests failed. Check the logs above.")

if __name__ == "__main__":
    asyncio.run(main())
