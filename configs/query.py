from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ClientQuery:
    phone_number: str
    account: str | None = None
    claimed_amount: Decimal | None = None


def normalize_phone(phone: str | None) -> str | None:
    if phone is None:
        return None
    return "".join(ch for ch in phone if ch.isdigit())


def transaction_matches_query(tx, query: ClientQuery) -> bool:
    tx_phone = normalize_phone(tx.phone)
    query_phone = normalize_phone(query.phone_number)

    if tx_phone != query_phone:
        return False

    if query.account and tx.account != query.account:
        return False

    return True