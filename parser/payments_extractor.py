from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
from typing import Iterable

from configs.payments_error_rules import ERROR_RULES
from parser.reader import read_log_records
from parser.time_utils import parse_log_timestamp


PAYMENT_SESSION_PKT_RE = re.compile(
    r"\b(?P<session_id>\d+)\.pkt\b",
    re.IGNORECASE,
)


@dataclass
class PaymentLogError:
    code: str
    title: str
    category: str
    severity: str
    line_no: int
    raw: str
    conclusion: str
    session_id: str | None = None
    timestamp: datetime | None = None


def extract_payment_session_id(text: str) -> str | None:
    match = PAYMENT_SESSION_PKT_RE.search(text)
    if not match:
        return None

    return match.group("session_id")


def detect_payment_errors_in_record(record: str, line_no: int) -> list[PaymentLogError]:
    result: list[PaymentLogError] = []

    timestamp = parse_log_timestamp(record)
    session_id = extract_payment_session_id(record)

    for rule in ERROR_RULES:
        if rule.pattern.search(record):
            result.append(
                PaymentLogError(
                    code=rule.code,
                    title=rule.title,
                    category=rule.category,
                    severity=rule.severity,
                    line_no=line_no,
                    raw=record,
                    conclusion=rule.conclusion,
                    session_id=session_id,
                    timestamp=timestamp,
                )
            )

    return result


def extract_payment_errors_from_records(records: Iterable[str]) -> list[PaymentLogError]:
    errors: list[PaymentLogError] = []

    for line_no, record in enumerate(records, start=1):
        errors.extend(detect_payment_errors_in_record(record, line_no))

    return errors


def extract_payment_errors(path: str | Path) -> list[PaymentLogError]:
    return extract_payment_errors_from_records(read_log_records(path))


def group_payment_errors_by_session(
    errors: list[PaymentLogError],
) -> dict[str, list[PaymentLogError]]:
    grouped: dict[str, list[PaymentLogError]] = {}

    for error in errors:
        if error.session_id is None:
            continue

        grouped.setdefault(error.session_id, []).append(error)

    return grouped