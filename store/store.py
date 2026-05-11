from .database import db_cursor
from datetime import datetime
import json

def create_tenant(name):
    with db_cursor() as cur:
        cur.execute("INSERT INTO tenants (name) VALUES (%s) RETURNING *", (name,))
        return dict(cur.fetchone())

def create_project(tenant_id, job_number=None, property_address=None, lot_number=None, client_name=None, phase=None, status=None, metadata=None):
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO projects (tenant_id, job_number, property_address, lot_number, client_name, phase, status, metadata) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *",
            (tenant_id, job_number, property_address, lot_number, client_name, phase, status, json.dumps(metadata or {}))
        )
        return dict(cur.fetchone())

def get_project_by_identifier(tenant_id, value):
    with db_cursor() as cur:
        cur.execute(
            "SELECT * FROM projects WHERE tenant_id = %s AND (job_number ILIKE %s OR property_address ILIKE %s OR lot_number ILIKE %s OR client_name ILIKE %s OR metadata::text ILIKE %s)",
            (tenant_id, f"%{value}%", f"%{value}%", f"%{value}%", f"%{value}%", f"%{value}%")
        )
        row = cur.fetchone()
        return dict(row) if row else None

def get_all_projects(tenant_id):
    with db_cursor() as cur:
        cur.execute("SELECT * FROM projects WHERE tenant_id = %s", (tenant_id,))
        return [dict(row) for row in cur.fetchall()]

def save_document(tenant_id, source, source_id, subject, author, timestamp, thread_id=None, project_id=None, version=1, needs_reply=False, needs_action=False, needs_documenting=False):
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO documents (tenant_id, project_id, source, source_id, subject, thread_id, author, timestamp, version, needs_reply, needs_action, needs_documenting) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT ON CONSTRAINT uq_document DO NOTHING RETURNING *",
            (tenant_id, project_id, source, source_id, subject, thread_id, author, timestamp, version, needs_reply, needs_action, needs_documenting)
        )
        row = cur.fetchone()
        return dict(row) if row else None

def stamp_document_project(document_id, project_id):
    with db_cursor() as cur:
        cur.execute("UPDATE documents SET project_id = %s WHERE document_id = %s", (project_id, document_id))

def update_document_status(document_id, needs_reply=False, needs_action=False, needs_documenting=False):
    with db_cursor() as cur:
        cur.execute(
            "UPDATE documents SET needs_reply = %s, needs_action = %s, needs_documenting = %s WHERE document_id = %s",
            (needs_reply, needs_action, needs_documenting, document_id)
        )

def save_chunks(chunks):
    with db_cursor() as cur:
        for chunk in chunks:
            cur.execute(
                "INSERT INTO chunks (tenant_id, document_id, project_id, text, embedding, chunk_position, source, author, timestamp) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (chunk['tenant_id'], chunk['document_id'], chunk.get('project_id'), chunk['text'], chunk['embedding'], chunk['chunk_position'], chunk['source'], chunk['author'], chunk['timestamp'])
            )

def stamp_chunks_project(document_id, project_id):
    with db_cursor() as cur:
        cur.execute("UPDATE chunks SET project_id = %s WHERE document_id = %s", (project_id, document_id))

def add_to_holding_queue(tenant_id, document_id, expires_at):
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO holding_queue (tenant_id, document_id, expires_at) VALUES (%s,%s,%s) RETURNING *",
            (tenant_id, document_id, expires_at)
        )
        return dict(cur.fetchone())

def get_pending_queue(tenant_id):
    with db_cursor() as cur:
        cur.execute("SELECT * FROM holding_queue WHERE tenant_id = %s AND status = 'pending'", (tenant_id,))
        return [dict(row) for row in cur.fetchall()]

def update_queue_status(queue_id, status):
    with db_cursor() as cur:
        cur.execute("UPDATE holding_queue SET status = %s WHERE queue_id = %s", (status, queue_id))

def save_deadline(tenant_id, project_id, description, due_date, source_document_id):
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO deadlines (tenant_id, project_id, description, due_date, source_document_id) VALUES (%s,%s,%s,%s,%s) RETURNING *",
            (tenant_id, project_id, description, due_date, source_document_id)
        )
        return dict(cur.fetchone())

def save_decision(tenant_id, project_id, description, date, source_document_id):
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO decisions (tenant_id, project_id, description, date, source_document_id) VALUES (%s,%s,%s,%s,%s) RETURNING *",
            (tenant_id, project_id, description, date, source_document_id)
        )
        return dict(cur.fetchone())

def save_action_item(tenant_id, project_id, description, assigned_to, due_date, source_document_id):
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO action_items (tenant_id, project_id, description, assigned_to, due_date, source_document_id) VALUES (%s,%s,%s,%s,%s,%s) RETURNING *",
            (tenant_id, project_id, description, assigned_to, due_date, source_document_id)
        )
        return dict(cur.fetchone())

def log_activity(tenant_id, project_id, type, description, user_id=None):
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO activity_feed (tenant_id, project_id, type, description, user_id) VALUES (%s,%s,%s,%s,%s)",
            (tenant_id, project_id, type, description, user_id)
        )
