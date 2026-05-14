"""
Triage step for the ingest pipeline.
Sits after normalise, before extract.
Checks the document envelope against the tenant's triage rules.
Returns True (process) or False (skip).
"""
import logging

logger = logging.getLogger(__name__)


def extract_sender_domain(sender):
    """Extract domain from an email address or sender string like 'Name <email@domain.com>'."""
    if not sender:
        return None
    # Handle 'Name <email@domain.com>' format
    if '<' in sender and '>' in sender:
        sender = sender.split('<')[1].split('>')[0]
    if '@' in sender:
        return sender.split('@')[1].strip().lower()
    return None


def check_triage(envelope, rules):
    """
    Check if a document should be processed or skipped.

    Args:
        envelope: Normalised document metadata dict
        rules: List of triage rule dicts from get_triage_rules()

    Returns:
        dict with:
            'pass': True (process) or False (skip)
            'matched_rule': the rule that triggered, or None
    """
    sender = (envelope.get('from') or envelope.get('author') or '').lower()
    sender_domain = extract_sender_domain(sender)
    subject = (envelope.get('subject') or envelope.get('file_name') or '').lower()

    allow_rules = [r for r in rules if r['rule_type'] == 'allow_sender']
    block_sender_rules = [r for r in rules if r['rule_type'] == 'block_sender']
    block_pattern_rules = [r for r in rules if r['rule_type'] == 'block_pattern']

    # 1. Whitelist checked first — always process
    for rule in allow_rules:
        value = rule['value'].lower()
        if rule['target'] == 'sender':
            if value in sender or (sender_domain and value == sender_domain):
                logger.debug(f"Triage ALLOW: {sender} matched allow rule '{value}'")
                return {'pass': True, 'matched_rule': rule}

    # 2. Block sender — domain or full address match
    for rule in block_sender_rules:
        value = rule['value'].lower()
        if rule['target'] == 'sender':
            if value == sender_domain or value == sender or value in sender:
                logger.info(f"Triage SKIP: {sender} matched block rule '{value}'")
                return {'pass': False, 'matched_rule': rule}

    # 3. Block pattern — substring match on target field
    for rule in block_pattern_rules:
        value = rule['value'].lower()
        if rule['target'] == 'sender' and value in sender:
            logger.info(f"Triage SKIP: sender '{sender}' matched pattern '{value}'")
            return {'pass': False, 'matched_rule': rule}
        elif rule['target'] == 'subject' and value in subject:
            logger.info(f"Triage SKIP: subject matched pattern '{value}'")
            return {'pass': False, 'matched_rule': rule}

    # 4. Default: process
    return {'pass': True, 'matched_rule': None}


def generate_block_rule(sender):
    """
    Given a sender string, generate a block_sender rule value (the domain).
    Returns None if domain can't be extracted.
    """
    domain = extract_sender_domain(sender)
    if not domain:
        return None
    return domain
