"""
Database Schema Validator

Validates database schema against model definitions to prevent
schema mismatches and ensure consistency across environments.
"""

import logging
from sqlalchemy import inspect
from app.models import Base

logger = logging.getLogger(__name__)

class SchemaValidator:
    """Validates database schema against model definitions"""
    
    def __init__(self, engine):
        self.engine = engine
        self.inspector = inspect(engine)
    
    def validate_all_tables(self):
        """Validate all model tables against database schema"""
        errors = []
        
        for table_name, table in Base.metadata.tables.items():
            if not self.inspector.has_table(table_name):
                errors.append(f"Table {table_name} does not exist")
                continue
                
            # Check columns
            db_columns = self.inspector.get_columns(table_name)
            db_column_names = {col['name'] for col in db_columns}
            model_column_names = {col.name for col in table.columns}
            
            # Missing columns
            missing_columns = model_column_names - db_column_names
            if missing_columns:
                errors.append(f"Table {table_name} missing columns: {missing_columns}")
            
            # Extra columns (warn but don't fail)
            extra_columns = db_column_names - model_column_names
            if extra_columns:
                logger.warning(f"Table {table_name} has extra columns: {extra_columns}")
        
        return errors
    
    def validate_specific_table(self, table_name):
        """Validate specific table schema"""
        if not self.inspector.has_table(table_name):
            return [f"Table {table_name} does not exist"]
        
        # Get model table
        if table_name not in Base.metadata.tables:
            return [f"Model for table {table_name} not found"]
        
        table = Base.metadata.tables[table_name]
        
        # Check columns
        db_columns = self.inspector.get_columns(table_name)
        db_column_names = {col['name'] for col in db_columns}
        model_column_names = {col.name for col in table.columns}
        
        errors = []
        
        # Missing columns
        missing_columns = model_column_names - db_column_names
        if missing_columns:
            errors.append(f"Table {table_name} missing columns: {missing_columns}")
        
        return errors
    
    def get_schema_summary(self):
        """Get summary of database schema"""
        summary = {
            'tables': [],
            'total_tables': 0,
            'missing_tables': [],
            'inconsistent_tables': []
        }
        
        for table_name, table in Base.metadata.tables.items():
            summary['total_tables'] += 1
            
            if not self.inspector.has_table(table_name):
                summary['missing_tables'].append(table_name)
                continue
            
            # Check for inconsistencies
            errors = self.validate_specific_table(table_name)
            if errors:
                summary['inconsistent_tables'].append({
                    'table': table_name,
                    'errors': errors
                })
            
            summary['tables'].append(table_name)
        
        return summary

