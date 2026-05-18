"""
Understand step — analyses documents with a land-development lens.
Extracts: relevance, project match, phase, classification, contacts,
facts, commitments, financial items, follow-ups, key quotes,
relationship tone, thread status, and action item updates.
"""
import anthropic
import os
import json
import re
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

UNDERSTAND_PROMPT = """You are analysing a document for Develo, a land development company in Adelaide, South Australia. Develo develops residential House and Land Packages — acquiring sites, subdividing, managing planning and construction, and selling to purchasers.

## Relevance

Relevant: property/site/project correspondence, contracts, invoices, quotes, council/government, contractors, consultants, legal, financial, sales, purchaser, builder, engineering, surveying, planning.

NOT relevant: marketing newsletters, automated notifications, spam, industry news not addressed to the business, social media, recruitment spam.

If not relevant: return {{"relevant": false, "relevance_reason": "brief reason"}}

## Land Development Phases

- **acquisition** — buying/securing land. Contracts of sale, due diligence, valuations, finance.
- **approvals** — DA, council, planning, referrals, conditions, amended plans.
- **delivery** — design, construction, inspections, contractor work, progress claims, defects.
- **division** — subdivision, survey plans, Section 51, LTO, deposited plans, easements.
- **sales** — contracts of sale, settlements, agent correspondence, purchaser management.

## Document Being Analysed

Source: {source}
Subject/Name: {subject}
From: {sender}
To: {recipient}
Date: {timestamp}

Content (first 3000 chars):
{content}

## Known Projects
{projects}

## Open Action Items
{action_items}

## What To Extract

Return a JSON object with ALL of the following keys. Every key MUST be present even if the value is an empty array or null.

### "relevant" (boolean)
### "relevance_reason" (string)

### "classification" (array, emails only)
One or more of: "needs_reply", "needs_action", "needs_documenting"

### "project_match" (string or null)
Project UUID from known projects. Match on address, lot numbers, DA numbers, client names, metadata. Null if no match.

### "summary" (string)
One sentence: what is this document and why does it matter.

### "phase" (string or null)
"acquisition", "approvals", "delivery", "division", "sales", or null.

### "thread_status" (string, always required)
- "new_request" — first contact or new topic
- "follow_up" — chasing or continuing a previous conversation
- "resolution" — confirming something is done/resolved/approved
- "informational" — FYI, no action expected

### "relationship_tone" (string, always required)
- "collaborative" — friendly, working together
- "transactional" — neutral, business as usual
- "adversarial" — dispute, threat, complaint, escalation language

### "contacts" (array)
People mentioned or involved. Each object:
- "name" — full name
- "email" — if visible
- "phone" — if visible
- "company" — organisation
- "role" — their function (e.g. "civil_engineer", "council_planner", "sales_agent", "solicitor", "builder", "purchaser", "surveyor", "certifier", "accountant", "energy_assessor")

Only extract contacts where you can identify at least a name AND (email OR company). Do not extract generic senders like "noreply@" or "info@".

### "facts" (array)
Each fact object:
- "type" — "action_item", "deadline", "decision", "condition", "financial", "risk"
- "description" — plain language
- "due_date" — ISO date if stated or calculable, null otherwise
- "due_date_basis" — "explicit", "calculated", "inferred", or null
- "urgency" — "critical", "high", "normal", or null
- "assigned_to_name" — person responsible if identifiable, null otherwise
- "source_quote" — key phrase (under 30 words)

### "commitments" (array)
Promises made BY someone TO Develo. NOT Develo's own tasks. Each object:
- "who" — person or company making the promise
- "what" — what they committed to
- "by_when" — ISO date if stated, null otherwise
- "source_quote" — their exact words (under 30 words)

### "financial_items" (array)
Invoices, quotes, payment references. Each object:
- "type" — "invoice", "quote", "payment", "credit_note"
- "from_entity" — who is charging/quoting
- "amount" — number (no currency symbol, no commas)
- "gst_included" — boolean
- "invoice_number" — if stated
- "due_date" — ISO date if stated
- "status" — "quoted", "invoiced", "paid", "overdue", "disputed"

### "follow_ups" (array)
Expected responses. Each object:
- "who_should_respond" — person or role expected to respond
- "to_whom" — who is waiting for the response
- "regarding" — what needs responding to
- "by_when" — ISO date if stated or calculable
- "source_quote" — the request (under 30 words)

### "key_quotes" (array of strings)
The 1-3 most important sentences from the document. Exact text. These should be the sentences someone would want to read without reading the full document. Always include at least one key quote.

### "action_updates" (array)
If this document completes any open action items listed above:
- "action_id" — UUID
- "new_status" — "completed"
- "reason" — how this document resolves it

Only complete an action if clearly done — "will do" does NOT count.

IMPORTANT: You MUST return ALL keys listed above. If a section has no items, return an empty array []. Do not omit any keys.

Return ONLY valid JSON. No markdown, no commentary, no code fences."""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def understand(envelope, chunks, project_identifiers, open_action_items=None):
    text = ' '.join([c['text'] for c in chunks[:3]])[:3000]

    if open_action_items:
        ai_text = json.dumps([
            {
                'action_id': str(a['action_id']),
                'project_id': str(a.get('project_id', '')),
                'description': a['description'],
                'due_date': str(a.get('due_date', ''))
            }
            for a in open_action_items
        ], indent=2)
    else:
        ai_text = "No open action items."

    prompt = UNDERSTAND_PROMPT.format(
        source=envelope.get('source', 'unknown'),
        subject=envelope.get('subject') or envelope.get('file_name', 'unknown'),
        sender=envelope.get('from') or envelope.get('author', 'unknown'),
        recipient=envelope.get('to', 'unknown'),
        timestamp=envelope.get('timestamp', 'unknown'),
        content=text,
        projects=json.dumps(project_identifiers, indent=2),
        action_items=ai_text
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=3000,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text
    raw = re.sub(r'^```(?:json)?\s*', '', raw.strip())
    raw = re.sub(r'\s*```$', '', raw)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        logger.error(f"understand failed to parse JSON: {raw[:500]}")
        return _empty_result()

    return _validate(result)


def _empty_result():
    return {
        "relevant": True,
        "relevance_reason": "Failed to analyse - defaulting to relevant",
        "classification": [],
        "project_match": None,
        "facts": [],
        "summary": "Document analysis failed.",
        "phase": None,
        "thread_status": "informational",
        "relationship_tone": "transactional",
        "contacts": [],
        "commitments": [],
        "financial_items": [],
        "follow_ups": [],
        "key_quotes": [],
        "action_updates": [],
    }


def _validate(result):
    relevant = result.get("relevant", True)
    if not relevant:
        return {
            "relevant": False,
            "relevance_reason": str(result.get("relevance_reason", "")),
            "classification": [],
            "project_match": None,
            "facts": [],
            "summary": str(result.get("relevance_reason", "")),
            "phase": None,
            "thread_status": "informational",
            "relationship_tone": "transactional",
            "contacts": [],
            "commitments": [],
            "financial_items": [],
            "follow_ups": [],
            "key_quotes": [],
            "action_updates": [],
        }

    valid_classifications = {"needs_reply", "needs_action", "needs_documenting"}
    valid_fact_types = {"action_item", "deadline", "decision", "condition", "financial", "risk"}
    valid_urgencies = {"critical", "high", "normal", None}
    valid_phases = {"acquisition", "approvals", "delivery", "division", "sales", None}
    valid_tones = {"collaborative", "transactional", "adversarial"}
    valid_thread = {"new_request", "follow_up", "resolution", "informational"}

    classification = [c for c in result.get("classification", []) if c in valid_classifications]

    project_match = result.get("project_match")
    if project_match is not None and not isinstance(project_match, str):
        project_match = None

    phase = result.get("phase") if result.get("phase") in valid_phases else None
    thread_status = result.get("thread_status") if result.get("thread_status") in valid_thread else "informational"
    relationship_tone = result.get("relationship_tone") if result.get("relationship_tone") in valid_tones else "transactional"

    # Validate facts
    facts = []
    for f in result.get("facts", []):
        if not isinstance(f, dict) or f.get("type") not in valid_fact_types:
            continue
        facts.append({
            "type": f["type"],
            "description": str(f.get("description", "")),
            "due_date": f.get("due_date"),
            "due_date_basis": f.get("due_date_basis"),
            "urgency": f.get("urgency") if f.get("urgency") in valid_urgencies else None,
            "assigned_to_name": f.get("assigned_to_name"),
            "source_quote": str(f.get("source_quote", ""))[:200],
        })

    # Validate contacts
    contacts = []
    for c in result.get("contacts", []):
        if not isinstance(c, dict):
            continue
        name = c.get("name")
        email = c.get("email")
        company = c.get("company")
        if name and (email or company):
            contacts.append({
                "name": str(name),
                "email": str(email) if email else None,
                "phone": str(c.get("phone", "")) if c.get("phone") else None,
                "company": str(company) if company else None,
                "role": str(c.get("role", "")) if c.get("role") else None,
            })

    # Validate commitments
    commitments = []
    for cm in result.get("commitments", []):
        if not isinstance(cm, dict) or not cm.get("who") or not cm.get("what"):
            continue
        commitments.append({
            "who": str(cm["who"]),
            "what": str(cm["what"]),
            "by_when": cm.get("by_when"),
            "source_quote": str(cm.get("source_quote", ""))[:200],
        })

    # Validate financial items
    financial_items = []
    valid_fi_types = {"invoice", "quote", "payment", "credit_note"}
    valid_fi_status = {"quoted", "invoiced", "paid", "overdue", "disputed"}
    for fi in result.get("financial_items", []):
        if not isinstance(fi, dict) or fi.get("type") not in valid_fi_types:
            continue
        amount = fi.get("amount")
        if amount is not None:
            try:
                amount = float(str(amount).replace(",", "").replace("$", ""))
            except (ValueError, TypeError):
                amount = None
        financial_items.append({
            "type": fi["type"],
            "from_entity": str(fi.get("from_entity", "")),
            "amount": amount,
            "gst_included": bool(fi.get("gst_included", False)),
            "invoice_number": str(fi.get("invoice_number", "")) if fi.get("invoice_number") else None,
            "due_date": fi.get("due_date"),
            "status": fi.get("status") if fi.get("status") in valid_fi_status else "invoiced",
        })

    # Validate follow-ups
    follow_ups = []
    for fu in result.get("follow_ups", []):
        if not isinstance(fu, dict) or not fu.get("regarding"):
            continue
        follow_ups.append({
            "who_should_respond": str(fu.get("who_should_respond", "")),
            "to_whom": str(fu.get("to_whom", "")),
            "regarding": str(fu["regarding"]),
            "by_when": fu.get("by_when"),
            "source_quote": str(fu.get("source_quote", ""))[:200],
        })

    # Validate key quotes
    key_quotes = []
    for kq in result.get("key_quotes", []):
        if isinstance(kq, str) and len(kq.strip()) > 10:
            key_quotes.append(kq.strip()[:500])
    key_quotes = key_quotes[:3]

    # Validate action updates
    action_updates = []
    for u in result.get("action_updates", []):
        if not isinstance(u, dict):
            continue
        if u.get("action_id") and u.get("new_status") == "completed":
            action_updates.append({
                "action_id": str(u["action_id"]),
                "new_status": "completed",
                "reason": str(u.get("reason", "")),
            })

    return {
        "relevant": True,
        "relevance_reason": str(result.get("relevance_reason", "")),
        "classification": classification,
        "project_match": project_match,
        "facts": facts,
        "summary": str(result.get("summary", "")),
        "phase": phase,
        "thread_status": thread_status,
        "relationship_tone": relationship_tone,
        "contacts": contacts,
        "commitments": commitments,
        "financial_items": financial_items,
        "follow_ups": follow_ups,
        "key_quotes": key_quotes,
        "action_updates": action_updates,
    }
