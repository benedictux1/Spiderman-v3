"""
Startup Validation Checks

Validates system integrity on startup to catch issues early.
"""

import logging
import os
from app.utils.schema_validator import SchemaValidator
from app.utils.database import DatabaseManager

logger = logging.getLogger(__name__)

def validate_database_schema():
    """Validate database schema on startup"""
    logger.info("🔍 Validating database schema...")
    
    try:
        dm = DatabaseManager()
        validator = SchemaValidator(dm.engine)
        errors = validator.validate_all_tables()
        
        if errors:
            logger.error("❌ Database schema validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            raise Exception("Database schema validation failed")
        else:
            logger.info("✅ Database schema validation passed")
            
    except Exception as e:
        logger.error(f"❌ Schema validation error: {e}")
        raise

def validate_environment_variables():
    """Validate required environment variables"""
    logger.info("🔍 Validating environment variables...")
    
    required_vars = [
        'DATABASE_URL',
        'FLASK_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        raise Exception(f"Missing environment variables: {missing_vars}")
    else:
        logger.info("✅ Environment variables validation passed")

def validate_database_connectivity():
    """Validate database connectivity"""
    logger.info("🔍 Validating database connectivity...")
    
    try:
        dm = DatabaseManager()
        with dm.get_session() as session:
            # Test basic connectivity
            result = session.execute("SELECT 1").scalar()
            if result != 1:
                raise Exception("Database connectivity test failed")
        
        logger.info("✅ Database connectivity validation passed")
        
    except Exception as e:
        logger.error(f"❌ Database connectivity validation failed: {e}")
        raise

def startup_validation():
    """Run all startup validations"""
    logger.info("🚀 Starting system validation...")
    
    try:
        # 1. Environment variables
        validate_environment_variables()
        
        # 2. Database connectivity
        validate_database_connectivity()
        
        # 3. Database schema
        validate_database_schema()
        
        logger.info("🎉 All startup validations passed!")
        return True
        
    except Exception as e:
        logger.error(f"💥 Startup validation failed: {e}")
        return False

def get_system_health():
    """Get comprehensive system health status"""
    health_status = {
        'overall': 'healthy',
        'checks': {},
        'errors': []
    }
    
    try:
        # Environment variables check
        try:
            validate_environment_variables()
            health_status['checks']['environment'] = 'healthy'
        except Exception as e:
            health_status['checks']['environment'] = 'unhealthy'
            health_status['errors'].append(f"Environment: {e}")
        
        # Database connectivity check
        try:
            validate_database_connectivity()
            health_status['checks']['database_connectivity'] = 'healthy'
        except Exception as e:
            health_status['checks']['database_connectivity'] = 'unhealthy'
            health_status['errors'].append(f"Database connectivity: {e}")
        
        # Database schema check
        try:
            validate_database_schema()
            health_status['checks']['database_schema'] = 'healthy'
        except Exception as e:
            health_status['checks']['database_schema'] = 'unhealthy'
            health_status['errors'].append(f"Database schema: {e}")
        
        # Overall status
        if any(check == 'unhealthy' for check in health_status['checks'].values()):
            health_status['overall'] = 'unhealthy'
        
        return health_status
        
    except Exception as e:
        health_status['overall'] = 'unhealthy'
        health_status['errors'].append(f"System health check failed: {e}")
        return health_status

