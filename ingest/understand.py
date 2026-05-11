import anthropic
import os
import json
import re
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def understand(envelope, chunks, project_identifiers):
    text = ' '.join([c['text'] for c in chunks[:3]])

    prompt = f"""You are analysing a document for a land development company called Develo.

Document source: {envelope.get('source')}
Document subject/name: {envelope.get('subject') or envelope.get('file_name')}
Content excerpt: {text[:2000]}

Known project identifiers:
{json.dumps(project_identifiers, indent=2)}

Return a JSON object with:
1. "classification": for emails only - array from ["needs_reply", "needs_action", "needs_documenting"]. Empty array for Drive files.
2. "project_match": matching project_id if found, otherwise null
3. "facts": array of structured facts, each with "type" (decision/deadline/action_item), "description", and "date" (ISO format string if found, otherwise null)

Return only valid JSON, no other text."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text
    raw = re.sub(r'^```(?:json)?\s*', '', raw.strip())
    raw = re.sub(r'\s*```$', '', raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logging.error(f"understand failed to parse JSON: {raw}")
        return {"classification": [], "project_match": None, "facts": []}
