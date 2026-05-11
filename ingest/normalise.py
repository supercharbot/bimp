import uuid
from datetime import datetime

def normalise_email(raw_email):
    return {
        'document_id': str(uuid.uuid4()),
        'source': 'gmail',
        'source_id': raw_email.get('message_id'),
        'from': raw_email.get('from'),
        'to': raw_email.get('to'),
        'subject': raw_email.get('subject'),
        'timestamp': raw_email.get('timestamp', datetime.utcnow()),
        'thread_id': raw_email.get('thread_id'),
        'attachment_ids': raw_email.get('attachment_ids', []),
        'project_id': None,
        'status': None,
        'version': 1
    }

def normalise_drive(raw_file):
    return {
        'document_id': str(uuid.uuid4()),
        'source': 'drive',
        'source_id': raw_file.get('file_id'),
        'author': raw_file.get('author'),
        'file_name': raw_file.get('file_name'),
        'file_type': raw_file.get('file_type'),
        'timestamp': raw_file.get('timestamp', datetime.utcnow()),
        'folder_path': raw_file.get('folder_path'),
        'project_id': None,
        'status': None,
        'version': 1
    }
