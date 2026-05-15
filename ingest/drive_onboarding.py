"""
Drive onboarding module.
Scans the Develo shared drive and processes all supported files
through the ingest pipeline.

Usage:
    cd ~/bimp && source venv/bin/activate
    python3 -m ingest.drive_onboarding --tenant-id <uuid>
"""
import logging
import argparse
from datetime import datetime
from shared.google_client import get_drive_service
from .pipeline import run_pipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

DEVELO_DRIVE_ID = '0AEbziIBtyuWAUk9PVA'
BATCH_SIZE = 25

SUPPORTED_TYPES = {
    'application/pdf': 'pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'application/msword': 'docx',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
    'application/vnd.ms-excel.sheet.macroenabled.12': 'xlsx',
    'application/vnd.google-apps.document': 'google-doc',
    'text/plain': 'txt',
    'text/html': 'html',
}

SKIP_TYPES = {
    'application/vnd.google-apps.folder',
    'image/jpeg', 'image/png', 'image/vnd.dwg',
    'application/zip', 'application/octet-stream',
    'application/x-koan', 'video/mp4', 'video/quicktime',
    'message/rfc822',
}


def fetch_all_files(service):
    all_files = []
    page_token = None
    while True:
        results = service.files().list(
            corpora='drive',
            driveId=DEVELO_DRIVE_ID,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            pageSize=1000,
            pageToken=page_token,
            fields='files(id,name,mimeType,modifiedTime,owners,parents,size),nextPageToken'
        ).execute()
        all_files.extend(results.get('files', []))
        page_token = results.get('nextPageToken')
        if not page_token:
            break
    return all_files


def get_folder_path(service, file_parents, folder_cache):
    if not file_parents:
        return ''
    parent_id = file_parents[0]
    if parent_id in folder_cache:
        return folder_cache[parent_id]
    try:
        folder = service.files().get(
            fileId=parent_id,
            supportsAllDrives=True,
            fields='name,parents'
        ).execute()
        parent_path = get_folder_path(service, folder.get('parents', []), folder_cache)
        path = f"{parent_path}/{folder['name']}" if parent_path else folder['name']
        folder_cache[parent_id] = path
        return path
    except Exception:
        folder_cache[parent_id] = ''
        return ''


def download_file(service, file_id, mime_type):
    if 'google-apps' in mime_type:
        export_mime = 'text/csv' if 'spreadsheet' in mime_type else 'text/plain'
        content = service.files().export(fileId=file_id, mimeType=export_mime).execute()
        return content if isinstance(content, bytes) else content.encode('utf-8')
    else:
        return service.files().get_media(fileId=file_id, supportsAllDrives=True).execute()


def match_project_by_folder(folder_path, projects):
    """Match a file to a project based on its folder path."""
    path_lower = folder_path.lower()
    for p in projects:
        addr = (p.get('property_address') or '').lower()
        if addr and len(addr) > 5 and addr in path_lower:
            return str(p['project_id'])
        lot = (p.get('lot_number') or '').lower()
        if lot and len(lot) > 2 and lot in path_lower:
            return str(p['project_id'])
        job = (p.get('job_number') or '').lower()
        if job and len(job) > 2 and job in path_lower:
            return str(p['project_id'])
    return None


def run_drive_onboarding(tenant_id, dry_run=False):
    service = get_drive_service()

    logger.info(f"Scanning Develo Drive ({DEVELO_DRIVE_ID})...")
    all_files = fetch_all_files(service)
    logger.info(f"Found {len(all_files)} total files")

    # Filter to supported types
    processable = []
    skipped_type = 0
    for f in all_files:
        mime = f.get('mimeType', '')
        if mime in SUPPORTED_TYPES:
            processable.append(f)
        elif mime in SKIP_TYPES:
            skipped_type += 1
        else:
            logger.debug(f"Unknown type skipped: {mime} ({f['name']})")
            skipped_type += 1

    logger.info(f"Processable: {len(processable)}, Skipped (unsupported type): {skipped_type}")

    if dry_run:
        for f in processable[:20]:
            mime = f.get('mimeType', '')
            logger.info(f"  Would process: {f['name']} ({SUPPORTED_TYPES.get(mime, mime)})")
        logger.info(f"Dry run complete. {len(processable)} files would be processed.")
        return

    # Load projects for folder matching
    from store.store import get_all_projects
    projects = get_all_projects(tenant_id)
    logger.info(f"Loaded {len(projects)} projects for folder matching")

    # Process
    folder_cache = {}
    processed = 0
    failed = 0
    duplicates = 0
    folder_matched = 0

    for i, f in enumerate(processable):
        file_id = f['id']
        mime = f.get('mimeType', '')
        file_type = SUPPORTED_TYPES.get(mime, 'unknown')
        name = f['name']

        try:
            logger.info(f"[{i+1}/{len(processable)}] {name} ({file_type})")

            folder_path = get_folder_path(service, f.get('parents', []), folder_cache)
            file_bytes = download_file(service, file_id, mime)

            raw_file = {
                'file_id': file_id,
                'file_name': name,
                'file_type': file_type,
                'author': f.get('owners', [{}])[0].get('displayName', 'unknown'),
                'timestamp': datetime.fromisoformat(f['modifiedTime'].replace('Z', '+00:00')) if f.get('modifiedTime') else datetime.utcnow(),
                'folder_path': folder_path,
            }

            # Skip SS (superseded) folders — store metadata only
            if '/ss/' in folder_path.lower() or folder_path.lower().endswith('/ss') or folder_path.lower() == 'ss':
                from store.store import save_document
                save_document(
                    tenant_id=tenant_id, source='drive', source_id=file_id,
                    subject=name, author=raw_file['author'],
                    timestamp=raw_file['timestamp'], thread_id=folder_path
                )
                logger.info(f'  SS folder — metadata only')
                processed += 1
                continue

            # Try folder-based project matching
            matched_project = match_project_by_folder(folder_path, projects)
            if matched_project:
                folder_matched += 1

            doc_id = run_pipeline(tenant_id, raw_file, 'drive', file_bytes=file_bytes,
                                  folder_project_id=matched_project)

            if doc_id:
                processed += 1
            else:
                duplicates += 1

        except Exception as e:
            logger.error(f"Failed: {name} — {e}")
            failed += 1

        if (i + 1) % BATCH_SIZE == 0:
            logger.info(f"Progress: {i+1}/{len(processable)} ({processed} ok, {duplicates} dup, {failed} fail)")

    logger.info(f"Drive onboarding complete: {processed} processed, {duplicates} duplicates, {failed} failed, {folder_matched} folder-matched out of {len(processable)}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run BIMP Drive onboarding')
    parser.add_argument('--tenant-id', required=True, help='Tenant UUID')
    parser.add_argument('--dry-run', action='store_true', help='List files without processing')
    args = parser.parse_args()
    run_drive_onboarding(args.tenant_id, dry_run=args.dry_run)
