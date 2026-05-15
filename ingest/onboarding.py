"""
Onboarding module for new tenants.
Fetches last month of email from the connected inbox,
processes in batches of 50. Each batch builds triage rules
that filter subsequent batches.

Usage:
    cd ~/bimp && source venv/bin/activate
    python3 -m ingest.onboarding --tenant-id <uuid>
"""
import logging
import argparse
from datetime import datetime, timedelta
from shared.google_client import get_gmail_service
from .triggers import fetch_email_content
from .pipeline import run_pipeline
from store.triage_store import get_triage_rules

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

BATCH_SIZE = 50


def fetch_message_ids(service, after_date, before_date=None):
    """
    Fetch all message IDs from INBOX within a date range.
    Returns list of message ID strings.
    """
    query = f"in:inbox after:{after_date.strftime('%Y/%m/%d')}"
    if before_date:
        query += f" before:{before_date.strftime('%Y/%m/%d')}"

    message_ids = []
    page_token = None

    while True:
        result = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=500,
            pageToken=page_token
        ).execute()

        messages = result.get('messages', [])
        message_ids.extend([m['id'] for m in messages])

        page_token = result.get('nextPageToken')
        if not page_token:
            break

    return message_ids


def run_onboarding(tenant_id):
    """
    Run the onboarding process for a tenant.

    1. Fetch all email IDs from the last month
    2. Process in batches of 50
    3. First batch: skip_triage=True (no rules exist yet)
    4. Subsequent batches: triage rules applied, filtering grows
    """
    service = get_gmail_service()
    three_months_ago = datetime.utcnow() - timedelta(days=30)

    logger.info(f"Onboarding tenant {tenant_id}: fetching emails since {three_months_ago.date()}")

    message_ids = fetch_message_ids(service, after_date=three_months_ago)
    total = len(message_ids)
    logger.info(f"Found {total} emails to process")

    if total == 0:
        logger.info("No emails found. Onboarding complete.")
        return

    # Process in batches
    processed = 0
    skipped = 0
    failed = 0
    batch_number = 0

    for i in range(0, total, BATCH_SIZE):
        batch = message_ids[i:i + BATCH_SIZE]
        batch_number += 1
        is_first_batch = (batch_number == 1)

        rules = get_triage_rules(tenant_id)
        logger.info(
            f"Batch {batch_number}: {len(batch)} emails "
            f"({len(rules)} triage rules active, "
            f"{'no triage' if is_first_batch else 'triage enabled'})"
        )

        for msg_id in batch:
            try:
                email_data = fetch_email_content(service, msg_id)
                doc_id = run_pipeline(
                    tenant_id=tenant_id,
                    raw_input=email_data,
                    input_type='email',
                    skip_triage=is_first_batch
                )
                if doc_id:
                    processed += 1
                else:
                    skipped += 1
            except Exception as e:
                logger.error(f"Failed to process email {msg_id}: {e}")
                failed += 1

        rules_after = get_triage_rules(tenant_id)
        new_rules = len(rules_after) - len(rules)
        if new_rules > 0:
            logger.info(f"Batch {batch_number} added {new_rules} new triage rules")

    logger.info(
        f"Onboarding complete: {processed} processed, {skipped} skipped, "
        f"{failed} failed out of {total} total"
    )
    final_rules = get_triage_rules(tenant_id)
    logger.info(f"Final triage rules count: {len(final_rules)}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run BIMP onboarding for a tenant')
    parser.add_argument('--tenant-id', required=True, help='Tenant UUID')
    args = parser.parse_args()
    run_onboarding(args.tenant_id)
