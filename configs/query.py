from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ClientQuery:
    phone_number: str | None = None
    account: str | None = None
    claimed_amount: Decimal | None = None


def normalize_digits(value: str | None) -> str | None:
    if value is None:
        return None

    digits = "".join(ch for ch in value if ch.isdigit())
    return digits or None


def transaction_matches_query(tx, query: ClientQuery) -> bool:
    query_phone = normalize_digits(query.phone_number)
    query_account = normalize_digits(query.account)

    tx_phone = normalize_digits(tx.phone)
    tx_account = normalize_digits(tx.account)

    if query_phone is None and query_account is None:
        return False

    if query_phone is not None and tx_phone == query_phone:
        return True

    if query_account is not None and tx_account == query_account:
        return True

    return False