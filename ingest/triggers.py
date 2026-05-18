"""
Gmail: Pub/Sub pull subscriber (event-driven).
Drive: Polls Develo Drive shared drive every 5 minutes.
Usage: cd ~/bimp && source venv/bin/activate && python3 -m ingest.triggers
"""
import base64
import json
import logging
import os
import threading
import time
from datetime import datetime

from google.cloud import pubsub_v1
from shared.google_client import get_gmail_service, get_drive_service, get_credentials
from ingest.pipeline import run_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = 'bimp-495600'
GMAIL_SUB = f'projects/{PROJECT_ID}/subscriptions/bimp-gmail-pull'
TENANT_ID = '2a1f5bad-7bfe-4494-9a3c-3de218bcaee1'
DEVELO_DRIVE_ID = '0AEbziIBtyuWAUk9PVA'
STATE_FILE = os.path.expanduser('~/bimp/.trigger_state.json')
DRIVE_POLL_INTERVAL = 300

# Attachment types we can extract text from
EXTRACTABLE_MIMES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
    'text/plain',
    'text/csv',
    'text/html',
}

# Skip these — images, signatures, inline content
SKIP_MIMES = {
    'image/png', 'image/jpeg', 'image/gif', 'image/bmp', 'image/webp',
    'application/pkcs7-signature', 'application/pgp-signature',
}

# Max attachment size to download (10MB)
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {'last_history_id': None, 'drive_page_token': None, 'processed_ids': []}


def save_state(state):
    state['processed_ids'] = state['processed_ids'][-500:]
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)


def fetch_email_content(service, msg_id):
    msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    headers = {h['name'].lower(): h['value'] for h in msg['payload'].get('headers', [])}

    body = ''
    html = ''
    attachment_meta = []

    def walk_parts(parts):
        nonlocal body, html
        for part in parts:
            mime = part.get('mimeType', '')
            data = part.get('body', {}).get('data')
            if mime == 'text/plain' and data:
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif mime == 'text/html' and data:
                html = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif part.get('filename') and part['body'].get('attachmentId'):
                attachment_meta.append({
                    'filename': part['filename'],
                    'mime_type': mime,
                    'attachment_id': part['body']['attachmentId'],
                    'size': part['body'].get('size', 0),
                })
            if 'parts' in part:
                walk_parts(part['parts'])

    payload = msg['payload']
    if 'parts' in payload:
        walk_parts(payload['parts'])
    elif payload.get('body', {}).get('data'):
        data = payload['body']['data']
        if payload.get('mimeType') == 'text/html':
            html = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        else:
            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

    # Download extractable attachments
    attachments = []
    for att in attachment_meta:
        mime = att['mime_type'].lower()
        filename = att['filename'].lower()
        size = att.get('size', 0)

        # Skip images and signatures
        if mime in SKIP_MIMES:
            continue

        # Skip oversized attachments
        if size > MAX_ATTACHMENT_SIZE:
            logger.warning(f"Skipping oversized attachment: {att['filename']} ({size} bytes)")
            continue

        # Check if extractable by mime type or file extension
        is_extractable = mime in EXTRACTABLE_MIMES
        if not is_extractable:
            if filename.endswith(('.pdf', '.docx', '.doc', '.xlsx', '.xls', '.txt', '.csv')):
                is_extractable = True

        if is_extractable:
            try:
                att_response = service.users().messages().attachments().get(
                    userId='me', messageId=msg_id, id=att['attachment_id']
                ).execute()
                att_bytes = base64.urlsafe_b64decode(att_response['data'])
                attachments.append({
                    'filename': att['filename'],
                    'mime_type': att['mime_type'],
                    'attachment_id': att['attachment_id'],
                    'data': att_bytes,
                })
                logger.info(f"Downloaded attachment: {att['filename']} ({len(att_bytes)} bytes)")
            except Exception as e:
                logger.warning(f"Failed to download attachment {att['filename']}: {e}")
        else:
            logger.debug(f"Skipping non-extractable attachment: {att['filename']} ({mime})")

    return {
        'message_id': msg_id,
        'from': headers.get('from', ''),
        'to': headers.get('to', ''),
        'subject': headers.get('subject', ''),
        'timestamp': datetime.utcfromtimestamp(int(msg['internalDate']) / 1000),
        'thread_id': msg.get('threadId'),
        'body': body,
        'html': html,
        'attachments': attachments,
        'attachment_ids': [a['attachment_id'] for a in attachment_meta],
    }


def handle_gmail_notification(message, state):
    data = json.loads(message.data.decode('utf-8'))
    new_history_id = data.get('historyId')
    if not new_history_id:
        return

    service = get_gmail_service()

    if not state['last_history_id']:
        state['last_history_id'] = new_history_id
        save_state(state)
        logger.info(f"Initial history ID recorded: {new_history_id}")
        return

    try:
        history = service.users().history().list(
            userId='me',
            startHistoryId=state['last_history_id'],
            historyTypes=['messageAdded'],
            labelId='INBOX'
        ).execute()
    except Exception as e:
        logger.error(f"History fetch failed: {e}")
        state['last_history_id'] = new_history_id
        save_state(state)
        return

    for record in history.get('history', []):
        for msg in record.get('messagesAdded', []):
            msg_id = msg['message']['id']
            if msg_id in state['processed_ids']:
                continue
            try:
                logger.info(f"Processing email: {msg_id}")
                email_data = fetch_email_content(service, msg_id)
                doc_id = run_pipeline(TENANT_ID, email_data, 'email')
                if doc_id:
                    logger.info(f"Email ingested: {msg_id} -> doc {doc_id}")
                state['processed_ids'].append(msg_id)
            except Exception as e:
                logger.error(f"Failed to process email {msg_id}: {e}")

    state['last_history_id'] = new_history_id
    save_state(state)


def poll_drive(state):
    service = get_drive_service()

    if not state.get('drive_page_token'):
        token = service.changes().getStartPageToken(
            driveId=DEVELO_DRIVE_ID,
            supportsAllDrives=True
        ).execute()
        state['drive_page_token'] = token['startPageToken']
        save_state(state)
        logger.info(f"Initial Drive page token: {state['drive_page_token']}")
        return

    try:
        changes = service.changes().list(
            pageToken=state['drive_page_token'],
            driveId=DEVELO_DRIVE_ID,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            fields="nextPageToken, newStartPageToken, changes(fileId, file(id, name, mimeType, modifiedTime, owners, parents))"
        ).execute()
    except Exception as e:
        logger.error(f"Drive changes failed: {e}")
        return

    for change in changes.get('changes', []):
        f = change.get('file')
        if not f:
            continue
        file_id = f['id']
        if file_id in state['processed_ids']:
            continue

        try:
            logger.info(f"Processing Drive file: {f['name']}")
            mime = f.get('mimeType', '')
            file_bytes = None

            if 'google-apps' in mime:
                export_mime = 'text/csv' if 'spreadsheet' in mime else 'text/plain'
                content = service.files().export(
                    fileId=file_id, mimeType=export_mime
                ).execute()
                file_bytes = content if isinstance(content, bytes) else content.encode('utf-8')
                file_type = 'csv' if 'spreadsheet' in mime else 'txt'
            else:
                content = service.files().get_media(
                    fileId=file_id, supportsAllDrives=True
                ).execute()
                file_bytes = content if isinstance(content, bytes) else content.encode('utf-8')
                file_type = mime.split('/')[-1] if mime else 'unknown'

            raw_file = {
                'file_id': file_id,
                'file_name': f['name'],
                'file_type': file_type,
                'author': f.get('owners', [{}])[0].get('displayName', 'unknown'),
                'timestamp': datetime.fromisoformat(f['modifiedTime'].replace('Z', '+00:00')),
                'folder_path': ','.join(f.get('parents', []))
            }

            doc_id = run_pipeline(TENANT_ID, raw_file, 'drive', file_bytes=file_bytes)
            if doc_id:
                logger.info(f"Drive file ingested: {f['name']} -> doc {doc_id}")
            state['processed_ids'].append(file_id)

        except Exception as e:
            logger.error(f"Failed to process Drive file {f.get('name')}: {e}")

    state['drive_page_token'] = changes.get('newStartPageToken', state['drive_page_token'])
    save_state(state)


def drive_poll_loop(state):
    logger.info(f"Drive polling started (every {DRIVE_POLL_INTERVAL}s, Develo Drive only)")
    while True:
        try:
            poll_drive(state)
        except Exception as e:
            logger.error(f"Drive poll error: {e}")
        time.sleep(DRIVE_POLL_INTERVAL)


def run_triggers():
    creds = get_credentials()
    state = load_state()

    # Start Drive polling in background thread
    drive_thread = threading.Thread(target=drive_poll_loop, args=(state,), daemon=True)
    drive_thread.start()

    # Gmail Pub/Sub pull subscriber (foreground)
    subscriber = pubsub_v1.SubscriberClient(credentials=creds)

    def gmail_callback(message):
        try:
            handle_gmail_notification(message, state)
            message.ack()
        except Exception as e:
            logger.error(f"Gmail callback error: {e}")
            message.nack()

    future = subscriber.subscribe(GMAIL_SUB, callback=gmail_callback)
    logger.info("Listening for Gmail notifications + polling Drive...")

    try:
        future.result()
    except KeyboardInterrupt:
        future.cancel()
        logger.info("Triggers stopped.")


if __name__ == '__main__':
    run_triggers()
