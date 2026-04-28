import re
from typing import List, Dict, Pattern

ERROR_PATTERNS: Dict[str, Pattern[str]] = {
    'Lenght_error': re.compile(r'Lenght_error', re.IGNORECASE),
    '#28': re.compile(r'#28', re.IGNORECASE),
    'stacker_opened=false': re.compile(r'stacker_opened\s*=\s*false', re.IGNORECASE),
}

SESSION_RE = re.compile(r'\bSESSION\s*=\s*([^,\s]+)', re.IGNORECASE)
PHONE_RE = re.compile(r'\bNUMBER\s*=\s*(\+?\d{9,15})', re.IGNORECASE)
ACCOUNT_RE = re.compile(r'\bACCOUNT\s*=\s*([^,\s]+)', re.IGNORECASE)

GENERIC_ERROR_RE = re.compile(r'([A-Za-z0-9_]+error[A-Za-z0-9_]*)', re.IGNORECASE)

BILL_RE = re.compile(r'(\d+)\s+TJS\s+(\d+)')

AMOUNTALL_RE = re.compile(r"AMOUNTALL_TJS\s*=\s*(\d+(?:\.\d+)?)", re.IGNORECASE)

CHEQUE_AMOUNT_RE = re.compile(r"Сумма\s*:\s*(\d+(?:\.\d+)?)\s*TJS", re.IGNORECASE)

CHEQUE_CREDITED_RE = re.compile(r"Зачислено\s*:\s*(\d+(?:\.\d+)?)\s*TJS",re.IGNORECASE)

CHEQUE_COMMISSION_RE = re.compile( r"Комиссия\s*:\s*(\d+(?:\.\d+)?)\s*TJS", re.IGNORECASE)

SESSION_START_INFO_RE = re.compile(r"GetNewSessionNumber", re.IGNORECASE)

PAYMENT_START_RE = re.compile(r"New\s+payment\s+started", re.IGNORECASE)

PAYMENT_COMPLETE_RE = re.compile(r"PaymentComplete\s*\.?\s*html|PaymentComplete\.html", re.IGNORECASE)

INIT_PAYMENT_COMPLETE_RE = re.compile(r"Initializing\s+payment\s+complete", re.IGNORECASE)

NAMED_FIELDS_RE = re.compile(r"NamedFields\s*:", re.IGNORECASE)

CHEQUE_INFO_RE = re.compile(r"Cheque\s+info\s*:", re.IGNORECASE)

def detect_errors(line: str) -> List[str]:
    """Detect error codes present in a log line.

    First, all known error patterns are tested; if they match, their keys are
    added to the result. Then, any unknown tokens containing the substring
    'error' are extracted using a generic pattern. This function may return
    multiple error codes for a single line.

    Args:
        line: The log line to analyze.

    Returns:
        A list of canonical error code strings detected in the line.
    """
    found: List[str] = []
    # Check for known errors
    for key, pattern in ERROR_PATTERNS.items():
        if pattern.search(line):
            found.append(key)
    # Look for unknown error tokens
    for match in GENERIC_ERROR_RE.findall(line):
        canonical_key = match
        # Avoid duplicates, ignoring case
        lower_known = {k.lower() for k in found}
        if canonical_key.lower() not in lower_known:
            found.append(canonical_key)
    return found
