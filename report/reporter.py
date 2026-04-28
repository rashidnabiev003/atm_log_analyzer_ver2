from decimal import Decimal
from configs.query import ClientQuery
from configs.models import Transaction


def format_investigation_report(result: dict) -> str:
    query: ClientQuery = result["query"]
    transactions: list[Transaction] = result["transactions"]

    parts: list[str] = []

    parts.append("ОТЧЕТ ПО КЛИЕНТУ")
    parts.append(f"Телефон: {query.phone_number}")
    parts.append(f"Аккаунт: {query.account or 'не указан'}")
    parts.append(
        f"Заявленная сумма: {query.claimed_amount if query.claimed_amount is not None else 'не указана'}"
    )
    parts.append(f"Найдено транзакций: {len(transactions)}")
    parts.append("")

    if not transactions:
        parts.append("По указанным данным транзакции не найдены.")
        return "\n".join(parts)

    for idx, tx in enumerate(transactions, start=1):
        parts.append(f"--- Транзакция {idx} ---")
        parts.append(tx.report())

        # Сравнение с заявленной клиентом суммой включаем только если она задана.
        if query.claimed_amount is not None:
            detected = Decimal(str(tx.total_inserted))
            diff = query.claimed_amount - detected
            parts.append("")
            parts.append("Сравнение с заявленной суммой клиента:")
            parts.append(f"- Клиент заявил: {query.claimed_amount} TJS")
            parts.append(f"- По логам купюр: {detected} TJS")
            parts.append(f"- Разница: {diff} TJS")
        else:
            parts.append("")
            parts.append("Сравнение с заявленной суммой клиента: пропущено, сумма не указана.")

        parts.append("")

    return "\n".join(parts)


def print_investigation_report(result: dict) -> None:
    print(format_investigation_report(result))
