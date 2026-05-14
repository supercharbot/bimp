"""
Understand step — analyses documents with a land-development lens.
Direct Claude API call with a fixed domain prompt.
Returns structured intelligence: relevance, classification, project match, facts,
and action item updates (auto-completion of tasks).
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

UNDERSTAND_PROMPT = """You are analysing a document for a land development company. Your job is to determine if this document is relevant to the business, and if so, extract structured intelligence from it.

## Relevance

A document is relevant if it directly relates to:
- A property, site, or development project
- A contractual, financial, or legal matter involving the business
- A regulatory or council matter
- Work being done by a contractor, consultant, or supplier for the business
- Internal business operations (team communication about projects, invoices, quotes)

A document is NOT relevant if it is:
- Marketing, newsletters, or promotional material (even if the topic is property or development)
- Automated system notifications (Google Drive shares, calendar invites, security alerts)
- Personal or unrelated correspondence
- Spam or bulk email
- Industry news, articles, or thought pieces not addressed to the business directly

If the document is not relevant, return: {{"relevant": false, "relevance_reason": "brief reason"}}
If relevant, continue with full analysis below.

## Land Development Phases

Classify which phase this document relates to:

### Acquisition
Buying or securing land for development.
Key documents: contracts of sale, option agreements, due diligence reports, title searches, valuation reports, finance approvals, vendor/agent correspondence, feasibility studies.
Key signals: settlement dates, option expiry, purchase price, contract conditions, cooling-off periods, sunset clauses.

### Approvals
Getting permission to develop the land.
Key documents: development applications, council correspondence, planning reports, referral agency responses, conditions of approval, amended plans, representations.
Key signals: DA numbers, assessment references, lodgement dates, information requests, conditions, approval/refusal, appeal deadlines, referral triggers.
Relevant bodies: council planning departments, SCAP, SA Water, SAPN, CFS, EPA, DEW, DPTI, NativVeg.

### Delivery
Designing and building the development.
Key documents: engineering plans, architectural drawings, contractor quotes, invoices, site inspection reports, progress claims, variation requests, practical completion certificates, defect notices, building certifier correspondence.
Key signals: construction timelines, inspection dates, payment schedules, variations, defect liability periods, insurance certificates, safety reports.

### Division
Subdividing the land into individual lots.
Key documents: survey plans, plan of division, Section 51 clearance applications, LTO lodgement, deposited plans, easement documents, community title schemes.
Key signals: lot/allotment numbers, deposited plan numbers, Section 51 requirements, LTO references, plan sealing dates, clearance conditions.

### Sales
Selling the developed lots.
Key documents: contracts of sale, settlement statements, agent agreements, marketing materials (from the business's own agent, not inbound), handover documentation, defect rectification.
Key signals: settlement dates, deposit amounts, contract conditions, sunset clauses, buyer correspondence.

## Document Being Analysed

Source: {source}
Subject/Name: {subject}
From: {sender}
Date: {timestamp}

Content:
{content}

## Known Projects

{projects}

## Open Action Items

These are tasks currently open across all projects. If this document resolves or completes any of them, include the action_id in action_updates.

{action_items}

## What To Extract

Return a JSON object with these keys:

### "relevant" (boolean)
Is this document relevant to a land development business? If false, include "relevance_reason" and stop.

### "relevance_reason" (string)
Brief explanation of why the document is or is not relevant.

### "classification" (array, emails only)
One or more of:
- "needs_reply" — sender expects a response
- "needs_action" — something must be done (submit documents, pay invoice, attend inspection, meet a deadline)
- "needs_documenting" — contains a decision, approval, condition, or fact worth recording

### "project_match" (string or null)
The project UUID from the known projects list if the document relates to one.
Match on: property address (including partial), lot/allotment numbers, DA number, CT reference, job number, council reference, client name, or anything in project metadata.
Null if no confident match.

### "summary" (string)
One or two sentences: what is this document and why does it matter.

### "phase" (string or null)
Which phase: "acquisition", "approvals", "delivery", "division", "sales", or null.

### "facts" (array)
Each fact is an object with:
- "type" — one of: "action_item", "deadline", "decision", "condition", "financial", "risk"
- "description" — plain language summary
- "due_date" — ISO 8601 date if stated or calculable, null otherwise
- "due_date_basis" — "explicit" (date stated), "calculated" (e.g. 28 days from notice date), "inferred" (estimate), or null
- "urgency" — "critical" (regulatory deadline, settlement, DA condition), "high" (client commitment, upcoming inspection), "normal" (routine), or null
- "source_quote" — the key phrase from the document supporting this fact (under 30 words)

### "action_updates" (array)
If this document completes any open action items listed above, include them here. Each entry:
- "action_id" — the UUID of the action item being resolved
- "new_status" — "completed"
- "reason" — brief explanation of how this document resolves the action item

Only mark an action item as completed if the document clearly shows the task is done — e.g. requested documents are attached, payment is confirmed, inspection is completed. A reply saying "will do" or "working on it" does NOT complete the task.

### Deadline Calculation
When a document says "within X days of this notice" or "within X days of [event]", calculate the actual date if the event date is known. State the basis in due_date_basis.
"Prior to" or "before" conditions are hard blockers — mark as critical urgency.

Return only valid JSON. No markdown, no commentary, no code fences."""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def understand(envelope, chunks, project_identifiers, open_action_items=None):
    """
    Analyse a document with a land-development lens.

    Args:
        envelope: Document metadata dict (source, subject/file_name, from, timestamp, etc.)
        chunks: List of chunk dicts with 'text' key
        project_identifiers: List of project dicts for matching
        open_action_items: List of open action item dicts (optional)

    Returns:
        Dict with relevant, classification, project_match, facts, summary, phase, action_updates
    """
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
        sender=envelope.get('from', 'unknown'),
        timestamp=envelope.get('timestamp', 'unknown'),
        content=text,
        projects=json.dumps(project_identifiers, indent=2),
        action_items=ai_text
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
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
        "relevance_reason": "Failed to analyse — defaulting to relevant",
        "classification": [],
        "project_match": None,
        "facts": [],
        "summary": "Document analysis failed.",
        "phase": None,
        "action_updates": [],
    }


def _validate(result):
    """Ensure the result has all expected keys with correct types."""

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
            "action_updates": [],
        }

    valid_classifications = {"needs_reply", "needs_action", "needs_documenting"}
    valid_fact_types = {"action_item", "deadline", "decision", "condition", "financial", "risk"}
    valid_urgencies = {"critical", "high", "normal", None}
    valid_phases = {"acquisition", "approvals", "delivery", "division", "sales", None}

    classification = result.get("classification", [])
    if not isinstance(classification, list):
        classification = []
    classification = [c for c in classification if c in valid_classifications]

    project_match = result.get("project_match")
    if project_match is not None and not isinstance(project_match, str):
        project_match = None

    phase = result.get("phase")
    if phase not in valid_phases:
        phase = None

    raw_facts = result.get("facts", [])
    if not isinstance(raw_facts, list):
        raw_facts = []

    facts = []
    for f in raw_facts:
        if not isinstance(f, dict):
            continue
        fact_type = f.get("type")
        if fact_type not in valid_fact_types:
            continue
        fact = {
            "type": fact_type,
            "description": str(f.get("description", "")),
            "due_date": f.get("due_date"),
            "due_date_basis": f.get("due_date_basis"),
            "urgency": f.get("urgency") if f.get("urgency") in valid_urgencies else None,
            "source_quote": str(f.get("source_quote", ""))[:200],
        }
        facts.append(fact)

    raw_updates = result.get("action_updates", [])
    if not isinstance(raw_updates, list):
        raw_updates = []

    action_updates = []
    for u in raw_updates:
        if not isinstance(u, dict):
            continue
        action_id = u.get("action_id")
        new_status = u.get("new_status")
        if action_id and new_status == "completed":
            action_updates.append({
                "action_id": str(action_id),
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
        "action_updates": action_updates,
    }
