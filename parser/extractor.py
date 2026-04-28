from typing import Iterable, List, Optional, Iterator

from configs import patterns
from configs.models import Transaction, Bill, DetectedError
from configs.error_rules import ERROR_RULES
from session.sessionizer import split_sessions


def extract_transactions(lines: Iterable[str]) -> List[Transaction]:
    transactions: List[Transaction] = []

    for session_lines in split_sessions(lines):
        # Extract session‑wide fields
        session_id: Optional[str] = None
        phone: Optional[str] = None
        account: Optional[str] = None
        for line in session_lines:
            if 'GetNewSessionNumber' in line:
                if not session_id:
                    m = patterns.SESSION_RE.search(line) if hasattr(patterns, 'SESSION_RE') else None
                    if m:
                        session_id = m.group(1)
                if not phone:
                    m = patterns.PHONE_RE.search(line) if hasattr(patterns, 'PHONE_RE') else None
                    if m:
                        phone = m.group(1)
                if not account:
                    m = patterns.ACCOUNT_RE.search(line) if hasattr(patterns, 'ACCOUNT_RE') else None
                    if m:
                        account = m.group(1)

        # State variables for transactions within this session
        current_tx: Optional[Transaction] = None
        last_tx: Optional[Transaction] = None

        for line_no, line in enumerate(session_lines, start=1):
            # Start of payment
            if 'New payment started' in line:
                # If a transaction is already in progress, finalize it as incomplete
                if current_tx:
                    transactions.append(current_tx)
                    last_tx = current_tx
                current_tx = Transaction(session_id=session_id, phone=phone, account=account)
                continue

            # Completion markers
            if (
                'PaymentComplete.html' in line
                or 'Initializing payment complete' in line
            ):
                if current_tx:
                    current_tx.completed = True
                    transactions.append(current_tx)
                    last_tx = current_tx
                    current_tx = None
                continue

            # Within active payment
            if current_tx:
                # Bills
                bill_match = patterns.BILL_RE.search(line)
                if bill_match:
                    denom = int(bill_match.group(1))
                    count = int(bill_match.group(2))
                    current_tx.bills.append(Bill(denomination=denom, count=count))
                    continue
                # Error codes
                errors = detect_errors_in_line(line, line_no)
                if errors:
                    current_tx.errors.extend(errors)
                # NamedFields expected amount
                amt_match = patterns.AMOUNTALL_RE.search(line)
                if amt_match:
                    try:
                        current_tx.expected_amount = float(amt_match.group(1))
                    except ValueError:
                        pass
                    continue

            # Outside active payment, associate cheque details with last transaction
            if current_tx is None and last_tx:
                cheque_amount = patterns.CHEQUE_AMOUNT_RE.search(line)
                if cheque_amount:
                    try:
                        last_tx.expected_amount = float(cheque_amount.group(1))
                    except ValueError:
                        pass
                    continue
                cheque_credited = patterns.CHEQUE_CREDITED_RE.search(line)
                if cheque_credited:
                    try:
                        last_tx.credited_amount = float(cheque_credited.group(1))
                    except ValueError:
                        pass
                    continue

        # Finalize any open transaction at end of session
        if current_tx:
            transactions.append(current_tx)

    return transactions

def detect_errors_in_line(line: str, line_no: int) -> list[DetectedError]:
    result = []

    for rule in ERROR_RULES:
        if rule.pattern.search(line):
            result.append(
                DetectedError(
                    code=rule.code,
                    title=rule.title,
                    category=rule.category,
                    severity=rule.severity,
                    line_no=line_no,
                    raw=line,
                    conclusion=rule.conclusion,
                )
            )

    return result