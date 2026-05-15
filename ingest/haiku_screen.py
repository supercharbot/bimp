import anthropic
import os
import json
import re
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
HAIKU_MODEL = "claude-haiku-4-5-20251001"
KNOWN_DOMAIN = "develo.net.au"

SCREEN_PROMPT = """You are a mail filter for a land development company. Decide if this document is genuine business correspondence or noise.

NOISE (return false):
- Marketing emails, newsletters, promotional content
- Automated system notifications (Google, Microsoft, Xero, software platforms)
- Subscription confirmations, password resets, security alerts
- Industry news digests, property market updates not addressed to the business
- Bulk email, mailing lists, no-reply senders
- Social media notifications
- Calendar sharing notifications, automated meeting summaries from platforms

GENUINE (return true):
- Emails from/to councils, contractors, consultants, clients, agents, solicitors
- Invoices, quotes, purchase orders
- Project correspondence (plans, reports, approvals, inspections)
- Government or regulatory correspondence
- Any email that mentions a specific property, address, project, or job

Source: {source}
Subject: {subject}
From: {sender}
Date: {timestamp}

First 500 words of content:
{content}

Return ONLY valid JSON: {{"pass": true}} or {{"pass": false, "reason": "brief reason"}}"""


def is_known_user(email_str):
    if not email_str:
        return False
    email_str = email_str.lower()
    if '<' in email_str and '>' in email_str:
        email_str = email_str.split('<')[1].split('>')[0]
    return email_str.endswith(f"@{KNOWN_DOMAIN}")


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5))
def screen_document(envelope, text):
    sender = envelope.get('from') or envelope.get('author') or ''
    recipient = envelope.get('to') or ''

    if is_known_user(sender):
        logger.info(f"Haiku skip: known sender ({sender})")
        return {'pass': True, 'reason': 'known_user'}

    content_preview = ' '.join(text.split()[:500])

    prompt = SCREEN_PROMPT.format(
        source=envelope.get('source', 'unknown'),
        subject=envelope.get('subject') or envelope.get('file_name', 'unknown'),
        sender=sender,
        timestamp=envelope.get('timestamp', 'unknown'),
        content=content_preview
    )

    response = client.messages.create(
        model=HAIKU_MODEL,
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    # Extract JSON from response
    json_match = re.search(r"\{[^}]+\}", raw)
    if json_match:
        raw = json_match.group(0)
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)

    try:
        result = json.loads(raw)
        passed = result.get('pass', True)
        reason = result.get('reason', '')
        logger.info(f"Haiku screen: {'PASS' if passed else 'FAIL'} - {envelope.get('subject', '')} ({reason})")
        return {'pass': passed, 'reason': reason}
    except json.JSONDecodeError:
        logger.warning(f"Haiku screen parse failed, defaulting to pass: {raw[:200]}")
        return {'pass': True, 'reason': 'parse_error'}
