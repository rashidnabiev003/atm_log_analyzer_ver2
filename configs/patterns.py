import re

### DPS PATTERNS
SESSION_RE = re.compile(r'\bSESSION\s*=\s*([^,\s]+)', re.IGNORECASE)
PHONE_RE = re.compile(r'\bNUMBER\s*=\s*(\+?\d{9,15})', re.IGNORECASE)
ACCOUNT_RE = re.compile(r'\bACCOUNT\s*=\s*([^,\s]+)', re.IGNORECASE)

DPS_STACKED_BILL_RE = re.compile(
    r"\bStacked\s*:\s*(?P<denom>\d+(?:[.,]\d+)?)\s*TJS\s+Type\s+\d+",
    re.IGNORECASE,
)

DPS_NOTE_ADDED_RE = re.compile(
    r"\bNote\s+(?P<denom>\d+(?:[.,]\d+)?)\s*TJS\s+added\s+to\s+payment\b",
    re.IGNORECASE,
)

BILL_RE = re.compile(
    r"(?m)^\s*(?P<denom>\d{1,6})\s+TJS\s+(?P<count>\d{1,6})\s*$",
    re.IGNORECASE,
)

SESSION_START_INFO_RE = re.compile(r"GetNewSessionNumber", re.IGNORECASE)

PAYMENT_START_RE = re.compile(r"New\s+payment\s+started", re.IGNORECASE)

INIT_PAYMENT_COMPLETE_RE = re.compile(r"Initializing\s+payment\s+complete", re.IGNORECASE)

CHEQUE_FIELDS_BLOCK_RE = re.compile(
    r"Named\s*Fields\s*:"
    r"|Fields\s+for\s+Cheque\s*:"
    r"|TForm1\s*:\s*MakeTextForPrint"
    r"|AMOUNTALL(?:_TJS)?\s*[:=]"
    r"|COMISSION\s*[:=]",
    re.IGNORECASE,
)

PAYMENT_COMPLETE_RE = re.compile(
    r"Payment\s*finished\.?"
    r"|PaymentFinished\.?",
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
    rf"\bCOMISSION(?:_TJS)?\b\s*[:=]\s*{MONEY_VALUE_PATTERN}",
    re.IGNORECASE,
)

LOCAL_DATIME_RE = re.compile(
    r"\b(?:LOCAL_DATIME|DATETIME)\b"
    r"\s*[:=]\s*"
    r"[\"']?"
    r"(?P<value>"
    r"\d{2}[./]\d{2}[./]\d{4}"
    r"(?:[ T]+"
    r"\d{2}[:.]\d{2}[:.]\d{2}"
    r"(?:[.:]\d{1,6})?"
    r")"
    r")"
    r"[\"']?",
    re.IGNORECASE,
)

DPS_MAX_PAYMENT_AMOUNT_RE = re.compile(
    r"Maximum\s+amount\s+to\s+collect\s+in\s+this\s+payment\s*:\s*"
    r"(?P<value>\d+(?:[.,]\d+)?)",
    re.IGNORECASE,
)

#### VALIDATOR PATTERNS
VALIDATOR_DEVICE_START_RE = re.compile(
    r"Старт\s+работы\s+устройства",
    re.IGNORECASE,
)

VALIDATOR_ENABLE_BILL_RE = re.compile(
    r"\bENABLE\s+BILL\b"
)

VALIDATOR_DISABLE_BILL_RE = re.compile(
    r"\bDISABLE\s+BILL\b"
)

VALIDATOR_STATE_RE = re.compile(
    r"State\s*\[\s*(?P<state>\d+)\s*\]",
    re.IGNORECASE,
)

VALIDATOR_STACKED_NOMINAL_RE = re.compile(
    r"Stacked\s+nominal\s*=\s*(?P<value>\d+(?:[.,]\d+)?)",
    re.IGNORECASE,
)

LOG_TIMESTAMP_RE = re.compile(
    r"(?P<ts>\d{2}[./]\d{2}[./]\d{4}\s+\d{2}[.:]\d{2}[.:]\d{2}[.:]\d{3})"
)


### PARSERS

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

