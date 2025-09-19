-- Performance indexes for the Kith Platform
-- These indexes will dramatically speed up common queries

-- Index for contact lookups by user and tier (most common query)
CREATE INDEX CONCURRENTLY idx_contacts_user_tier ON contacts (user_id, tier);

-- Index for contact details lookups (used when loading full profiles)
CREATE INDEX CONCURRENTLY idx_contact_details_lookup ON contact_details (contact_id, category);

-- Index for searching contacts by name (used in search functionality)
CREATE INDEX CONCURRENTLY idx_contacts_name_search ON contacts USING gin(to_tsvector('english', full_name));

-- Index for raw logs with contact and date (used for audit trails)
CREATE INDEX CONCURRENTLY idx_raw_logs_contact_date ON raw_logs (contact_id, date DESC);

-- Index for contact tags (used when filtering by tags)
CREATE INDEX CONCURRENTLY idx_contact_tags_lookup ON contact_tags (contact_id, tag_id);

-- Index for telegram integration lookups
CREATE INDEX CONCURRENTLY idx_contacts_telegram ON contacts (telegram_username) WHERE telegram_username IS NOT NULL;

-- Index for contact relationships (used in graph visualization)
CREATE INDEX CONCURRENTLY idx_relationships_source ON contact_relationships (source_contact_id, target_contact_id);

-- Index for task status tracking
CREATE INDEX CONCURRENTLY idx_task_status_type ON task_status (task_type, status);

-- Update table statistics after adding indexes
ANALYZE contacts;
ANALYZE contact_details;
ANALYZE contact_tags;
ANALYZE raw_logs;
ANALYZE contact_relationships;
ANALYZE task_status;
