"""
Triage store functions.
Add these to store/store.py or import from here.
Follows existing store.py patterns: db_cursor, dict(row), tenant-scoped.
"""
from .database import db_cursor


def get_triage_rules(tenant_id):
    """Get all triage rules for a tenant."""
    with db_cursor() as cur:
        cur.execute(
            "SELECT * FROM triage_rules WHERE tenant_id = %s",
            (tenant_id,)
        )
        return [dict(row) for row in cur.fetchall()]


def add_triage_rule(tenant_id, rule_type, value, target='sender', source='auto'):
    """
    Add a triage rule. Ignores duplicates via ON CONFLICT.
    rule_type: 'block_sender', 'block_pattern', 'allow_sender'
    target: 'sender' or 'subject'
    source: 'auto' or 'manual'
    """
    with db_cursor() as cur:
        cur.execute(
            """INSERT INTO triage_rules (tenant_id, rule_type, value, target, source)
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT (tenant_id, rule_type, value, target) DO NOTHING
               RETURNING *""",
            (tenant_id, rule_type, value, target, source)
        )
        row = cur.fetchone()
        return dict(row) if row else None


def remove_triage_rule(rule_id):
    """Remove a triage rule by ID."""
    with db_cursor() as cur:
        cur.execute("DELETE FROM triage_rules WHERE rule_id = %s", (rule_id,))


def save_document_skipped(tenant_id, source, source_id, subject, author, timestamp,
                          thread_id=None, version=1):
    """
    Save a minimal document record for a triaged-out email.
    No project_id, no status flags, triage_status = 'skipped'.
    Uses same dedup constraint as save_document.
    """
    with db_cursor() as cur:
        cur.execute(
            """INSERT INTO documents
               (tenant_id, project_id, source, source_id, subject, thread_id,
                author, timestamp, version, needs_reply, needs_action,
                needs_documenting, triage_status)
               VALUES (%s, NULL, %s, %s, %s, %s, %s, %s, %s,
                       FALSE, FALSE, FALSE, 'skipped')
               ON CONFLICT ON CONSTRAINT uq_document DO NOTHING
               RETURNING *""",
            (tenant_id, source, source_id, subject, thread_id,
             author, timestamp, version)
        )
        row = cur.fetchone()
        return dict(row) if row else None
