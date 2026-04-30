from datetime import timedelta
from decimal import Decimal
from typing import Any

from configs.query import ClientQuery, transaction_matches_query


def amount_difference(tx, query: ClientQuery):
    if query.claimed_amount is None:
        return None

    detected = Decimal(str(tx.total_inserted))
    return query.claimed_amount - detected


def group_payment_errors_by_session(payment_errors: list[Any]) -> dict[str, list[Any]]:
    grouped: dict[str, list[Any]] = {}

    for error in payment_errors:
        session_id = getattr(error, "session_id", None)
        if session_id is None:
            continue

        grouped.setdefault(str(session_id), []).append(error)

    return grouped


def find_validator_cycles_for_transaction(
    tx,
    validator_cycles: list[Any],
    *,
    fallback_minutes: int = 10,
) -> list[Any]:
    if tx.started_at is None:
        return []

    tx_end = tx.completed_at or (tx.started_at + timedelta(minutes=fallback_minutes))

    matched = []

    for cycle in validator_cycles:
        cycle_start = getattr(cycle, "started_at", None)
        if cycle_start is None:
            continue

        if tx.started_at <= cycle_start <= tx_end:
            matched.append(cycle)

    return matched


def investigate(
    transactions,
    query: ClientQuery,
    *,
    payment_errors: list[Any] | None = None,
    validator_cycles: list[Any] | None = None,
):
    payment_errors = payment_errors or []
    validator_cycles = validator_cycles or []

    matched = [tx for tx in transactions if transaction_matches_query(tx, query)]

    payment_errors_by_session = group_payment_errors_by_session(payment_errors)

    transaction_reports = []

    for tx in matched:
        session_id = str(tx.session_id) if tx.session_id is not None else None

        related_payment_errors = (
            payment_errors_by_session.get(session_id, [])
            if session_id is not None
            else []
        )

        related_validator_cycles = find_validator_cycles_for_transaction(
            tx,
            validator_cycles,
        )

        transaction_reports.append(
            {
                "transaction": tx,
                "payment_errors": related_payment_errors,
                "validator_cycles": related_validator_cycles,
            }
        )

    return {
        "query": query,
        "transactions": matched,
        "transaction_reports": transaction_reports,
        "total_found": len(matched),
        "payment_errors_total": len(payment_errors),
        "validator_cycles_total": len(validator_cycles),
    }