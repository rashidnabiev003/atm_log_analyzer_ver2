from typing import Iterable, List, Optional
from configs import patterns
from configs.models import Transaction, Bill, DetectedError
from configs.dps_error_rules import ERROR_RULES
from session.sessionizer import split_sessions
from parser.time_utils import parse_log_timestamp

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


def extract_transactions(lines: Iterable[str]) -> List[Transaction]:
    transactions: List[Transaction] = []
    global_pending_errors: list[DetectedError] = []
    last_closed_tx: Optional[Transaction] = None

    for session_lines in split_sessions(lines):
        session_id: Optional[str] = None
        phone: Optional[str] = None
        account: Optional[str] = None

        for line in session_lines:
            if not session_id:
                m = patterns.SESSION_RE.search(line)
                if m:
                    session_id = m.group(1)

            if not phone:
                m = patterns.PHONE_RE.search(line)
                if m:
                    phone = m.group(1)

            if not account:
                m = patterns.ACCOUNT_RE.search(line)
                if m:
                    account = m.group(1)

        current_tx: Optional[Transaction] = None
        pending_errors: list[DetectedError] = []
        inside_cheque_fields = False

        for line_no, line in enumerate(session_lines, start=1):
            line_timestamp = parse_log_timestamp(line)
            line_errors = detect_errors_in_line(line, line_no)
            started_new_tx = False

            if patterns.PAYMENT_START_RE.search(line):
                if current_tx:
                    transactions.append(current_tx)
                    last_closed_tx = current_tx

                current_tx = Transaction(
                    session_id=session_id,
                    phone=phone,
                    account=account,
                    started_at=line_timestamp,
                )

                inside_cheque_fields = False
                started_new_tx = True

                if global_pending_errors:
                    current_tx.errors.extend(global_pending_errors)
                    global_pending_errors = []

                if pending_errors:
                    current_tx.errors.extend(pending_errors)
                    pending_errors = []

                if line_errors:
                    current_tx.errors.extend(line_errors)

            target_tx = current_tx

            if line_errors and not target_tx:
                if last_closed_tx is not None:
                    last_closed_tx.errors.extend(line_errors)
                else:
                    pending_errors.extend(line_errors)

            if patterns.INIT_PAYMENT_COMPLETE_RE.search(line):
                if current_tx:
                    current_tx.cash_collection_completed = True

            if target_tx:
                if line_errors and not started_new_tx:
                    target_tx.errors.extend(line_errors)

                for stacked_match in patterns.DPS_STACKED_BILL_RE.finditer(line):
                    value = patterns.parse_money(stacked_match.group("denom"))
                    if value is not None:
                        target_tx.dps_stacked_bill_values.append(value)

                for note_match in patterns.DPS_NOTE_ADDED_RE.finditer(line):
                    value = patterns.parse_money(note_match.group("denom"))
                    if value is None:
                        continue

                    if target_tx.bill_table_seen:
                        continue

                    row_key = f"DPS_NOTE:{value}:{line_no}"

                    if row_key not in target_tx.dps_note_bill_keys:
                        target_tx.dps_note_bill_keys.add(row_key)
                        target_tx.bills.append(Bill(denomination=int(value), count=1))

                for bill_match in patterns.BILL_RE.finditer(line):
                    denom = int(bill_match.group("denom"))
                    count = int(bill_match.group("count"))

                    if not target_tx.bill_table_seen:
                        target_tx.bills.clear()
                        target_tx.bill_row_keys.clear()
                        target_tx.bill_table_seen = True

                    row_key = f"TABLE:{denom}:TJS:{count}"

                    if row_key not in target_tx.bill_row_keys:
                        target_tx.bill_row_keys.add(row_key)
                        target_tx.bills.append(Bill(denomination=denom, count=count))

                payment_fields = patterns.parse_payment_fields(line)

                starts_cheque_fields = (
                    patterns.CHEQUE_FIELDS_BLOCK_RE.search(line) is not None
                    or "AMOUNTALL" in payment_fields
                    or "COMISSION" in payment_fields
                    or "LOCAL_DATETIME" in payment_fields
                )

                if starts_cheque_fields:
                    inside_cheque_fields = True


                if inside_cheque_fields and payment_fields:
                    target_tx.named_fields.update(payment_fields)

                    amount_all = payment_fields.get("AMOUNTALL")
                    amount = payment_fields.get("AMOUNT")
                    comission = payment_fields.get("COMISSION")
                    local_datetime = payment_fields.get("LOCAL_DATETIME")

                    parsed_amount_all = patterns.parse_money(amount_all)
                    parsed_amount = patterns.parse_money(amount)
                    parsed_comission = patterns.parse_money(comission)

                    if parsed_amount_all is not None:
                        target_tx.expected_amount = parsed_amount_all

                    if parsed_amount is not None:
                        target_tx.credited_amount = parsed_amount

                    if parsed_comission is not None:
                        target_tx.comission_amount = parsed_comission

                    if local_datetime:
                        target_tx.local_datetime = local_datetime

            if patterns.PAYMENT_COMPLETE_RE.search(line):
                if current_tx:
                    current_tx.completed = True
                    current_tx.completed_at = line_timestamp
                    transactions.append(current_tx)
                    last_closed_tx = current_tx
                    current_tx = None
                    inside_cheque_fields = False

        if current_tx:
            transactions.append(current_tx)
            last_closed_tx = current_tx

        if pending_errors:
            if last_closed_tx is not None:
                last_closed_tx.errors.extend(pending_errors)
            else:
                global_pending_errors.extend(pending_errors)
    
    return transactions
