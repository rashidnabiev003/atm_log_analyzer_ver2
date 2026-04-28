from typing import Iterable, List
from configs.models import Transaction


def format_transaction(tx: Transaction) -> str:
    """Return a detailed report string for a single transaction."""
    return tx.report()  # Delegate to the model's report method


def format_report(transactions: Iterable[Transaction]) -> str:
    """Concatenate formatted reports for multiple transactions."""
    parts: List[str] = []
    for idx, tx in enumerate(transactions, start=1):
        parts.append(f"--- Транзакция {idx} ---\n" + tx.report())
    return "\n\n".join(parts)


def print_report(transactions: Iterable[Transaction]) -> None:
    """Print a report for a list of transactions to stdout."""
    report = format_report(transactions)
    print(report)
