from .normalise import normalise_email, normalise_drive
from .extract import extract_text
from .chunk import chunk_text
from .embed import embed_chunks
from .understand import understand
from .triage import check_triage, generate_block_rule
from .haiku_screen import screen_document
from store.store import (
    save_document, save_chunks, stamp_document_project,
    stamp_chunks_project, add_to_holding_queue, get_all_projects,
    update_document_status, save_deadline, save_decision,
    save_action_item, log_activity, upsert_contact,
    link_contact_to_project, save_commitment, save_financial_item,
    save_follow_up, update_document_metadata
)
from store.triage_store import (
    get_triage_rules, add_triage_rule, save_document_skipped
)
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def _get_open_action_items(tenant_id):
    """Fetch all open action items for a tenant."""
    from store.database import db_cursor
    with db_cursor() as cur:
        cur.execute(
            "SELECT * FROM action_items WHERE tenant_id = %s AND status = 'open'",
            (tenant_id,)
        )
        return [dict(row) for row in cur.fetchall()]


def _complete_action_item(action_id, reason):
    """Mark an action item as completed."""
    from store.database import db_cursor
    with db_cursor() as cur:
        cur.execute(
            "UPDATE action_items SET status = 'completed' WHERE action_id = %s",
            (action_id,)
        )
        logger.info(f"Action item {action_id} completed: {reason}")


def _set_triage_status(document_id, status):
    """Update triage_status on a document."""
    from store.database import db_cursor
    with db_cursor() as cur:
        cur.execute(
            "UPDATE documents SET triage_status = %s WHERE document_id = %s",
            (status, document_id)
        )


def run_pipeline(tenant_id, raw_input, input_type, file_bytes=None, skip_triage=False, folder_project_id=None):
    """
    Run the full ingest pipeline.

    Args:
        tenant_id: UUID of the tenant
        raw_input: Raw email data dict or Drive file data dict
        input_type: 'email' or 'drive'
        file_bytes: Raw file bytes for Drive files or attachments
        skip_triage: If True, bypass triage (used during first onboarding batch)
    """
    # Step 1 — Normalise
    if input_type == 'email':
        envelope = normalise_email(raw_input)
        text = extract_text(raw_input, file_bytes)
    else:
        envelope = normalise_drive(raw_input)
        text = extract_text(envelope, file_bytes)

    # Step 2 — Triage
    if not skip_triage:
        rules = get_triage_rules(tenant_id)
        triage_result = check_triage(envelope, rules)

        if not triage_result['pass']:
            save_document_skipped(
                tenant_id=tenant_id,
                source=envelope['source'],
                source_id=envelope.get('source_id'),
                subject=envelope.get('subject') or envelope.get('file_name'),
                author=envelope.get('from') or envelope.get('author'),
                timestamp=envelope.get('timestamp'),
                thread_id=envelope.get('thread_id') or envelope.get('folder_path'),
                version=envelope.get('version', 1)
            )
            logger.info(
                f"Triage skipped: {envelope.get('subject') or envelope.get('file_name')} "
                f"(rule: {triage_result['matched_rule']['value']})"
            )
            return None


    # Step 2b - Haiku screening
    if text:
        screen_result = screen_document(envelope, text)
        if not screen_result['pass']:
            save_document_skipped(
                tenant_id=tenant_id,
                source=envelope['source'],
                source_id=envelope.get('source_id'),
                subject=envelope.get('subject') or envelope.get('file_name'),
                author=envelope.get('from') or envelope.get('author'),
                timestamp=envelope.get('timestamp'),
                thread_id=envelope.get('thread_id') or envelope.get('folder_path'),
                version=envelope.get('version', 1)
            )
            sender = envelope.get('from') or envelope.get('author')
            domain = generate_block_rule(sender)
            if domain:
                added = add_triage_rule(tenant_id, 'block_sender', domain)
                if added:
                    logger.info(f'Haiku auto-added triage rule: block {domain}')
            logger.info(f"Haiku screened out: {envelope.get('subject') or envelope.get('file_name')} ({screen_result['reason']})")
            return None

    # Step 3 — Extract
    if not text:
        logger.warning(f"No text extracted from document: {envelope.get('source_id')}")
        return None

    # Step 4 — Chunk
    chunks = chunk_text(text, envelope)

    # Step 5 — Embed
    chunks = embed_chunks(chunks)

    # Step 6 — Store
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
        logger.info(f"Duplicate document skipped: {envelope.get('source_id')}")
        return None

    document_id = doc['document_id']
    for chunk in chunks:
        chunk['tenant_id'] = tenant_id
        chunk['document_id'] = document_id

    save_chunks(chunks)
    _set_triage_status(document_id, 'passed')

    # Step 7 — Understand
    # If folder-matched, stamp project and skip expensive understand
    if folder_project_id:
        stamp_document_project(document_id, folder_project_id)
        stamp_chunks_project(document_id, folder_project_id)
        log_activity(tenant_id, folder_project_id, 'document_ingested',
                     f"Ingested {envelope.get('source')}: {envelope.get('subject') or envelope.get('file_name')} (folder-matched)")
        return document_id

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

    open_actions = _get_open_action_items(tenant_id)
    result = understand(envelope, chunks, project_identifiers, open_actions)

    # Auto-generate triage rule if understand says irrelevant
    if not result.get('relevant', True):
        sender = envelope.get('from') or envelope.get('author')
        domain = generate_block_rule(sender)
        if domain:
            added = add_triage_rule(tenant_id, 'block_sender', domain)
            if added:
                logger.info(f"Auto-added triage rule: block {domain}")
        _set_triage_status(document_id, 'irrelevant')

    # Step 8 — Project matching
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

    # Save phase and metadata from understand
    phase = result.get('phase')
    summary = result.get('summary')
    relationship_tone = result.get('relationship_tone')
    thread_status = result.get('thread_status')
    key_quotes = result.get('key_quotes')

    if phase:
        from store.database import db_cursor as _db_cursor
        with _db_cursor() as cur:
            cur.execute("UPDATE documents SET phase = %s WHERE document_id = %s", (phase, document_id))

    update_document_metadata(document_id, summary, relationship_tone, thread_status, key_quotes)

    # Step 9 — Classification (email only)
    if input_type == 'email':
        classification = result.get('classification', [])
        update_document_status(
            document_id=document_id,
            needs_reply='needs_reply' in classification,
            needs_action='needs_action' in classification,
            needs_documenting='needs_documenting' in classification
        )

    # Step 10 — Save structured facts
    for fact in result.get('facts', []):
        if fact['type'] == 'deadline':
            save_deadline(tenant_id, project_id, fact['description'],
                          fact.get('due_date'), document_id, fact.get('urgency'), fact.get('due_date_basis'))
        elif fact['type'] == 'decision':
            save_decision(tenant_id, project_id, fact['description'],
                          fact.get('due_date') or str(datetime.utcnow().date()),
                          document_id)
        elif fact['type'] == 'action_item':
            save_action_item(tenant_id, project_id, fact['description'],
                             None, fact.get('due_date'), document_id, fact.get('urgency'), fact.get('due_date_basis'))

    # Step 11 — Save contacts
    for contact in result.get('contacts', []):
        c = upsert_contact(tenant_id, contact['name'], contact.get('email'),
                           contact.get('phone'), contact.get('company'), contact.get('role'))
        if c and project_id:
            link_contact_to_project(project_id, c['contact_id'], contact.get('role'))

    # Step 12 — Save commitments
    for cm in result.get('commitments', []):
        save_commitment(tenant_id, project_id, cm['who'], cm['what'],
                        cm.get('by_when'), document_id, cm.get('source_quote'))

    # Step 13 — Save financial items
    for fi in result.get('financial_items', []):
        save_financial_item(tenant_id, project_id, fi['type'], fi['from_entity'],
                            fi.get('amount'), fi.get('gst_included', False),
                            fi.get('invoice_number'), fi.get('due_date'),
                            fi.get('status', 'invoiced'), document_id)

    # Step 14 — Save follow-ups
    for fu in result.get('follow_ups', []):
        save_follow_up(tenant_id, project_id, fu['who_should_respond'], fu['to_whom'],
                       fu['regarding'], fu.get('by_when'), document_id, fu.get('source_quote'))

    # Step 15 — Auto-complete action items
    for update in result.get('action_updates', []):
        _complete_action_item(update['action_id'], update['reason'])

    log_activity(tenant_id, project_id, 'document_ingested',
                 f"Ingested {envelope.get('source')}: {envelope.get('subject') or envelope.get('file_name')}")

    return document_id
