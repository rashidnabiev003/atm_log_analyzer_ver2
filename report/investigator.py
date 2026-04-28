from decimal import Decimal
from configs.query import ClientQuery, transaction_matches_query


def investigate(transactions, query: ClientQuery):
    matched = [tx for tx in transactions if transaction_matches_query(tx, query)]

    return {
        "query": query,
        "transactions": matched,
        "total_found": len(matched),
    }


def amount_difference(tx, query: ClientQuery):
    if query.claimed_amount is None:
        return None

    detected = Decimal(str(tx.total_inserted))
    return query.claimed_amount - detected