"""Add performance indexes

Revision ID: 4288915872ea
Revises: 77cd9dc6a008
Create Date: 2025-09-14 16:11:08.875370

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4288915872ea'
down_revision: Union[str, None] = '77cd9dc6a008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # User-based queries
    op.create_index('idx_contacts_user_id', 'contacts', ['user_id'])
    op.create_index('idx_contacts_user_tier', 'contacts', ['user_id', 'tier'])
    op.create_index('idx_contacts_user_name', 'contacts', ['user_id', 'full_name'])
    
    # Contact-based queries
    op.create_index('idx_raw_notes_contact', 'raw_notes', ['contact_id'])
    op.create_index('idx_synthesized_contact', 'synthesized_entries', ['contact_id'])
    op.create_index('idx_synthesized_category', 'synthesized_entries', ['contact_id', 'category'])
    
    # Time-based queries
    op.create_index('idx_raw_notes_created', 'raw_notes', ['created_at'])
    op.create_index('idx_synthesized_created', 'synthesized_entries', ['created_at'])
    op.create_index('idx_contacts_updated', 'contacts', ['updated_at'])
    
    # Search optimization (GIN indexes for full-text search)
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    op.create_index('idx_contacts_name_gin', 'contacts', ['full_name'], postgresql_using='gin', postgresql_ops={'full_name': 'gin_trgm_ops'})
    op.create_index('idx_synthesized_content_gin', 'synthesized_entries', ['content'], postgresql_using='gin', postgresql_ops={'content': 'gin_trgm_ops'})
    
    # Telegram integration
    op.create_index('idx_contacts_telegram_id', 'contacts', ['telegram_id'])
    op.create_index('idx_contacts_telegram_username', 'contacts', ['telegram_username'])
    
    # Task management
    op.create_index('idx_import_tasks_user_status', 'import_tasks', ['user_id', 'status'])
    op.create_index('idx_import_tasks_created', 'import_tasks', ['created_at'])


def downgrade() -> None:
    op.drop_index('idx_import_tasks_created')
    op.drop_index('idx_import_tasks_user_status')
    op.drop_index('idx_contacts_telegram_username')
    op.drop_index('idx_contacts_telegram_id')
    op.drop_index('idx_synthesized_content_gin')
    op.drop_index('idx_contacts_name_gin')
    op.drop_index('idx_contacts_updated')
    op.drop_index('idx_synthesized_created')
    op.drop_index('idx_raw_notes_created')
    op.drop_index('idx_synthesized_category')
    op.drop_index('idx_synthesized_contact')
    op.drop_index('idx_raw_notes_contact')
    op.drop_index('idx_contacts_user_name')
    op.drop_index('idx_contacts_user_tier')
    op.drop_index('idx_contacts_user_id')
