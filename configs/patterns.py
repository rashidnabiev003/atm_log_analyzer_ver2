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

BILL_RE = re.compile(
    r"(?m)^\s*(?P<denom>\d{1,6})\s+TJS\s+(?P<count>\d{1,6})\s*$",
    re.IGNORECASE,
)

SESSION_START_INFO_RE = re.compile(r"GetNewSessionNumber", re.IGNORECASE)

PAYMENT_START_RE = re.compile(r"New\s+payment\s+started", re.IGNORECASE)

PAYMENT_COMPLETE_RE = re.compile(
    r'PaymentComplete\s*\.?\s*html|PaymentComplete\.html|Payment\s*finished|PaymentFinished',
    re.IGNORECASE,
)

INIT_PAYMENT_COMPLETE_RE = re.compile(r"Initializing\s+payment\s+complete", re.IGNORECASE)

NAMED_FIELDS_RE = re.compile(
    r"\bNamed\s*Fields\s*:",
    re.IGNORECASE,
)

PAYMENT_COMPLETE_RE = re.compile(
    r"PaymentComplete\s*\.?\s*html|PaymentComplete\.html",
    re.IGNORECASE,
)

MONEY_VALUE_PATTERN = r"(?P<value>[+-]?\d+(?:[.,]\d+)?)"

AMOUNTALL_RE = re.compile(
    rf"\bAMOUNTALL(?:_TJS)?\b\s*[:=]\s*{MONEY_VALUE_PATTERN}",
    re.IGNORECASE,
)

AMOUNT_RE = re.compile(
    rf"\bAMOUNT\b\s*[:=]\s*{MONEY_VALUE_PATTERN}",
    re.IGNORECASE,
)

COMISSION_RE = re.compile(
    rf"\bCOMISSION\b\s*[:=]\s*{MONEY_VALUE_PATTERN}",
    re.IGNORECASE,
)

LOCAL_DATIME_RE = re.compile(
    r"\bLOCAL_DATIME\b\s*[:=]\s*"
    r"(?P<value>"
    r"\d{2}[./]\d{2}[./]\d{4}"
    r"(?:\s+\d{2}[:.]\d{2}[:.]\d{2}(?:[.:]\d{1,6})?)?"
    r")",
    re.IGNORECASE,
)


def detect_errors(line: str) -> List[str]:
    found: List[str] = []
    # Check for known errors
    for key, pattern in ERROR_PATTERNS.items():
        if pattern.search(line):
            found.append(key)
    return found


def parse_money(value: str | None) -> float | None:
    if value is None:
        return None

    cleaned = (
        value.strip()
        .replace(",", ".")
        .replace("TJS", "")
        .replace("tjs", "")
    )

    try:
        return float(cleaned)
    except ValueError:
        return None

def _first_value(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    if not match:
        return None
    return match.group("value").strip()

def parse_payment_fields(text: str) -> dict[str, str]:
    result: dict[str, str] = {}

    amount_all = _first_value(AMOUNTALL_RE, text)
    amount = _first_value(AMOUNT_RE, text)
    comission = _first_value(COMISSION_RE, text)
    local_datime = _first_value(LOCAL_DATIME_RE, text)

    if amount_all is not None:
        result["AMOUNTALL"] = amount_all

    if amount is not None:
        result["AMOUNT"] = amount

    if comission is not None:
        result["COMISSION"] = comission

    if local_datime is not None:
        result["LOCAL_DATETIME"] = local_datime

    return result

