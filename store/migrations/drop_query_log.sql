-- Migration: Drop query_log table (redundant with conversation_memory)
-- Run: sudo cp this to /tmp/ then sudo -u postgres psql -d bimp -f /tmp/drop_query_log.sql

DROP TABLE IF EXISTS query_log;
