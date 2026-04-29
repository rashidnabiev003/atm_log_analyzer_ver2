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

BILL_RE = re.compile(r'(\d+)\s+TJS\s+(\d+)')

SESSION_START_INFO_RE = re.compile(r"GetNewSessionNumber", re.IGNORECASE)

PAYMENT_START_RE = re.compile(r"New\s+payment\s+started", re.IGNORECASE)

PAYMENT_COMPLETE_RE = re.compile(
    r"PaymentComplete\s*\.?\s*html"
    r"|PaymentComplete\.html"
    r"|Payment\s*finished"
    r"|PaymentFinished",
    re.IGNORECASE,
)

INIT_PAYMENT_COMPLETE_RE = re.compile(r"Initializing\s+payment\s+complete", re.IGNORECASE)

MONEY_FIELD_RE = re.compile(
    r"\b(?P<key>"
    r"AMOUNTALL_TJS|AMOUNTALL|"
    r"AMOUNT_TJS|AMOUNT|"
    r"COMISSION_TJS|COMISSION|"
    r"COMMISSION_TJS|COMMISSION"
    r")"
    r"\s*[:=]\s*"
    r"(?P<value>[+-]?\d+(?:[.,]\d+)?)",
    re.IGNORECASE,
)

LOCAL_DATETIME_RE = re.compile(
    r"\b(?P<key>LOCAL_DATIME|LOCAL_DATETIME)"
    r"\s*[:=]\s*"
    r"(?P<value>"
    r"\d{2}[./]\d{2}[./]\d{4}"
    r"(?:\s+\d{2}[:.]\d{2}[:.]\d{2}(?:[.:]\d{1,6})?)?"
    r")",
    re.IGNORECASE,
)


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
    return found


def parse_payment_fields(line: str) -> dict[str, str]:
    """
    Парсинг системных полей платежа.

    На выходе нормализуем ключи:
    - AMOUNT_TJS -> AMOUNT
    - COMISSION_TJS / COMMISSION / COMMISSION_TJS -> COMISSION
    - LOCAL_DATIME -> LOCAL_DATETIME
    """
    result: dict[str, str] = {}

    aliases = {
        "AMOUNTALL_TJS": "AMOUNTALL_TJS",
        "AMOUNTALL": "AMOUNTALL",

        "AMOUNT_TJS": "AMOUNT",
        "AMOUNT": "AMOUNT",

        "COMISSION_TJS": "COMISSION",
        "COMISSION": "COMISSION",
        "COMMISSION_TJS": "COMISSION",
        "COMMISSION": "COMISSION",

        "LOCAL_DATIME": "LOCAL_DATETIME",
        "LOCAL_DATETIME": "LOCAL_DATETIME",
    }

    for match in MONEY_FIELD_RE.finditer(line):
        raw_key = match.group("key").upper()
        key = aliases.get(raw_key, raw_key)
        value = match.group("value").strip()
        result[key] = value

    for match in LOCAL_DATETIME_RE.finditer(line):
        raw_key = match.group("key").upper()
        key = aliases.get(raw_key, raw_key)
        value = match.group("value").strip()
        result[key] = value

    return result


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