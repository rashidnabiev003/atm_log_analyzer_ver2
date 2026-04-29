from typing import Iterable, List, Optional

from configs import patterns
from configs.models import Transaction, Bill, DetectedError
from configs.error_rules import ERROR_RULES
from session.sessionizer import split_sessions

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

    for session_lines in split_sessions(lines):
        # Extract session‑wide fields
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

        # State variables for transactions within this session
        current_tx: Optional[Transaction] = None
        last_tx: Optional[Transaction] = None
        pending_errors: list[DetectedError] = []


        for line_no, line in enumerate(session_lines, start=1):
            # 1. Старт нового платежа
            line_errors = detect_errors_in_line(line, line_no)

            if patterns.PAYMENT_START_RE.search(line):
                if current_tx:
                    transactions.append(current_tx)
                    last_tx = current_tx

                current_tx = Transaction(
                    session_id=session_id,
                    phone=phone,
                    account=account,
                )

                if pending_errors:
                    current_tx.errors.extend(pending_errors)
                    pending_errors = []
                
                if line_errors:
                    current_tx.errors.extend(line_errors)

                continue

            # Все факты после этого пытаемся привязать либо к активному платежу,
            # либо к последнему платежу, если активного уже нет.
            target_tx = current_tx or last_tx

            if target_tx:

                # 3. Купюры
                if line_errors:
                    target_tx.errors.extend(line_errors)

                bill_match = patterns.BILL_RE.search(line)
                if bill_match:
                    denom = int(bill_match.group(1))
                    count = int(bill_match.group(2))

                    row_key = f"{denom}:TJS:{count}"

                    if row_key not in target_tx.bill_row_keys:
                        target_tx.bill_row_keys.add(row_key)
                        target_tx.bills.append(Bill(denomination=denom, count=count))
                
                if target_tx.cash_collection_completed:
                    payment_fields = patterns.parse_payment_fields(line)
                else:
                    payment_fields = {}
                    
                if payment_fields:
                    
                    target_tx.named_fields.update(payment_fields)

                    amount_all = (
                        payment_fields.get("AMOUNTALL_TJS")
                        or payment_fields.get("AMOUNTALL")
                    )

                    amount = (
                        payment_fields.get("AMOUNT_TJS")
                        or payment_fields.get("AMOUNT")
                    )

                    comission = (
                        payment_fields.get("COMISSION_TJS")
                        or payment_fields.get("COMISSION")
                    )

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

            # 7. Завершение приема купюр — это не конец транзакции
            if patterns.INIT_PAYMENT_COMPLETE_RE.search(line):
                if current_tx:
                    current_tx.cash_collection_completed = True

            # 8. Настоящее завершение платежа
            if patterns.PAYMENT_COMPLETE_RE.search(line):
                if current_tx:
                    current_tx.completed = True
                    transactions.append(current_tx)
                    last_tx = current_tx
                    current_tx = None

        # Finalize any open transaction at end of session
        if current_tx:
            transactions.append(current_tx)

    return transactions
