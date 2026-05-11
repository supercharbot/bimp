from .normalise import normalise_email, normalise_drive
from .extract import extract_text
from .chunk import chunk_text
from .embed import embed_chunks
from .understand import understand
from store.store import (
    save_document, save_chunks, stamp_document_project,
    stamp_chunks_project, add_to_holding_queue, get_all_projects,
    update_document_status, save_deadline, save_decision,
    save_action_item, log_activity
)
from datetime import datetime, timedelta
import logging

def run_pipeline(tenant_id, raw_input, input_type, file_bytes=None):
    if input_type == 'email':
        envelope = normalise_email(raw_input)
        text = extract_text(raw_input, file_bytes)
    else:
        envelope = normalise_drive(raw_input)
        text = extract_text(envelope, file_bytes)

    if not text:
        logging.warning(f"No text extracted from document: {envelope.get('source_id')}")
        return None

    chunks = chunk_text(text, envelope)
    chunks = embed_chunks(chunks)

    doc = save_document(
        tenant_id=tenant_id,
        source=envelope['source'],
        source_id=envelope.get('source_id'),
        subject=envelope.get('subject') or envelope.get('file_name'),
        author=envelope.get('from') or envelope.get('author'),
        timestamp=envelope.get('timestamp'),
        thread_id=envelope.get('thread_id') or envelope.get('folder_path'),
        project_id=None,
        version=envelope.get('version', 1)
    )

    if doc is None:
        logging.info(f"Duplicate document skipped: {envelope.get('source_id')}")
        return None

    document_id = doc['document_id']
    for chunk in chunks:
        chunk['tenant_id'] = tenant_id
        chunk['document_id'] = document_id

    save_chunks(chunks)

    projects = get_all_projects(tenant_id)
    project_identifiers = [
        {
            'project_id': str(p['project_id']),
            'job_number': p['job_number'],
            'property_address': p['property_address'],
            'lot_number': p['lot_number'],
            'client_name': p['client_name'],
            'metadata': p.get('metadata', {})
        }
        for p in projects
    ]

    result = understand(envelope, chunks, project_identifiers)

    project_id = result.get('project_match')
    if project_id:
        stamp_document_project(document_id, project_id)
        stamp_chunks_project(document_id, project_id)
    else:
        add_to_holding_queue(
            tenant_id=tenant_id,
            document_id=document_id,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )

    if input_type == 'email':
        classification = result.get('classification', [])
        update_document_status(
            document_id=document_id,
            needs_reply='needs_reply' in classification,
            needs_action='needs_action' in classification,
            needs_documenting='needs_documenting' in classification
        )

    for fact in result.get('facts', []):
        if fact['type'] == 'deadline':
            save_deadline(tenant_id, project_id, fact['description'], fact.get('date'), document_id)
        elif fact['type'] == 'decision':
            save_decision(tenant_id, project_id, fact['description'], fact.get('date') or str(datetime.utcnow().date()), document_id)
        elif fact['type'] == 'action_item':
            save_action_item(tenant_id, project_id, fact['description'], None, fact.get('date'), document_id)

    log_activity(tenant_id, project_id, 'document_ingested', f"Ingested {envelope.get('source')}: {envelope.get('subject') or envelope.get('file_name')}")

    return document_id
