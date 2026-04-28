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

# Generic pattern for capturing unknown error tokens containing 'error'.
GENERIC_ERROR_RE = re.compile(r'([A-Za-z0-9_]+error[A-Za-z0-9_]*)', re.IGNORECASE)

# Regex for bill table entries: matches '<denom> TJS <count>'
BILL_RE = re.compile(r'(\d+)\s+TJS\s+(\d+)')

# Regex for expected amount in NamedFields: 'AMOUNTALL_TJS=...'
AMOUNTALL_RE = re.compile(r'AMOUNTALL_TJS=(\d+(?:\.\d+)?)')

# Regex for cheque info: 'Сумма : <amount> TJS'
CHEQUE_AMOUNT_RE = re.compile(r'Сумма\s*:\s*(\d+(?:\.\d+)?)\s*TJS', re.IGNORECASE)

# Regex for cheque credited: 'Зачислено : <amount> TJS'
CHEQUE_CREDITED_RE = re.compile(r'Зачислено\s*:\s*(\d+(?:\.\d+)?)\s*TJS', re.IGNORECASE)


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
