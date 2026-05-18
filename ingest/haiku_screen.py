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

SCREEN_PROMPT = """You are screening incoming email for a land development company called Develo based in Adelaide, South Australia. Develo develops residential House and Land Packages — they acquire sites, subdivide land, manage planning approvals, coordinate builders, and sell to purchasers.

The support@develo.net.au inbox receives both genuine business correspondence and noise. Your job is to classify this email.

REJECT (return false) — this is noise:
- Marketing emails, property newsletters, industry news digests
- Automated platform notifications (Google Workspace, Xero, MYOB, Slack, Trello, DocuSign admin, software updates)
- Subscription confirmations, password resets, security alerts, 2FA codes
- Bulk email from no-reply addresses, mailing lists
- Social media notifications
- Generic sales outreach or cold emails not about a specific Develo project
- Calendar sharing notifications from unknown parties
- Job application auto-responses, recruitment spam

ACCEPT (return true) — this is genuine business correspondence:
- Emails from councils, government agencies, SA Water, SAPN, DHUD, PlanSA, CFS, EPA
- Emails from builders, contractors, subcontractors, trades about specific work
- Invoices, quotes, purchase orders, payment confirmations
- Solicitor, conveyancer, or accountant correspondence
- Emails mentioning a specific property address, lot number, DA number, or project name
- Purchaser or sales agent correspondence
- Emails from engineers, surveyors, planners, energy assessors, arborists, certifiers
- Bank or lender correspondence (Beyond Bank, Bluestreak, HomeStart)
- Insurance correspondence
- Any email that references a real person by name in a business context

When uncertain, ACCEPT. It is better to process a marginal email than to miss genuine correspondence.

Source: {source}
Subject: {subject}
From: {sender}
Date: {timestamp}

First 300 words of content:
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

    if is_known_user(sender):
        logger.info(f"Haiku skip: known sender ({sender})")
        return {'pass': True, 'reason': 'known_user'}

    content_preview = ' '.join(text.split()[:300])

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
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)

    json_match = re.search(r'\{[^}]+\}', raw)
    if json_match:
        raw = json_match.group(0)

    try:
        result = json.loads(raw)
        passed = result.get('pass', True)
        reason = result.get('reason', '')
        logger.info(f"Haiku screen: {'PASS' if passed else 'FAIL'} - {envelope.get('subject', '')} ({reason})")
        return {'pass': passed, 'reason': reason}
    except json.JSONDecodeError:
        logger.warning(f"Haiku screen parse failed, defaulting to pass: {raw[:200]}")
        return {'pass': True, 'reason': 'parse_error'}
