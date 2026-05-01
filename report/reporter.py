from decimal import Decimal
from configs.query import ClientQuery
from configs.models import Transaction
from collections import Counter

def format_unique_errors(errors: list) -> str:
    if not errors:
        return "нет"

    grouped = {}

    for err in errors:
        key = (
            err.code,
            err.title,
            err.category,
            err.severity,
            err.conclusion,
        )

        if key not in grouped:
            grouped[key] = {
                "error": err,
                "count": 0,
            }

        grouped[key]["count"] += 1

    parts = []

    for item in grouped.values():
        err = item["error"]
        count = item["count"]

        count_suffix = f" x{count}" if count > 1 else ""

        parts.append(
            "\n".join(
                [
                    f"- [{err.severity}] {err.code}: {err.title}{count_suffix}",
                    f"  Категория: {err.category}",
                    f"  Время: {getattr(err, 'timestamp', None) or 'N/A'}",
                    f"  Строка: {err.line_no}",
                    f"  Вывод: {err.conclusion}",
                    f"  Пример фрагмента: {err.raw[:500]}",
                ]
            )
        )

    return "\n".join(parts)

def format_payment_errors(errors: list) -> str:
    return format_unique_errors(errors)


def format_validator_errors(errors: list) -> str:
    return format_unique_errors(errors)


def format_validator_cycles(cycles: list) -> str:
    if not cycles:
        return "нет"

    parts = []
    all_errors = []

    total_validator_stacked = 0.0

    for idx, cycle in enumerate(cycles, start=1):
        cycle_errors = getattr(cycle, "errors", [])
        all_errors.extend(cycle_errors)

        total_stacked = getattr(cycle, "total_stacked", 0.0)
        total_validator_stacked += total_stacked

        last_max_cash = getattr(cycle, "last_max_cash", None)

        parts.append(
            "\n".join(
                [
                    f"- Цикл приёма купюр {idx}",
                    f"  Начало: {cycle.started_at if cycle.started_at is not None else 'N/A'}",
                    f"  Конец: {cycle.finished_at if cycle.finished_at is not None else 'N/A'}",
                    f"  Завершён корректно: {'да' if cycle.is_complete else 'нет'}",
                    f"  Принято по Validator: {total_stacked:g} TJS",
                    f"  Последний MaxCash: {last_max_cash if last_max_cash is not None else 'N/A'}",
                ]
            )
        )

    parts.append(f"Итого принято по Validator: {total_validator_stacked:g} TJS")

    if all_errors:
        parts.append("Ошибки Validator:")
        parts.append(format_unique_errors(all_errors))

    return "\n".join(parts)


def format_investigation_report(result: dict) -> str:
    query: ClientQuery = result["query"]
    transaction_reports = result.get("transaction_reports")

    if transaction_reports is None:
        transactions: list[Transaction] = result["transactions"]
        transaction_reports = [
            {
                "transaction": tx,
                "payment_errors": [],
                "validator_cycles": [],
            }
            for tx in transactions
        ]

    parts: list[str] = []

    parts.append("ОТЧЕТ ПО КЛИЕНТУ")
    parts.append(f"Телефон: {query.phone_number}")
    parts.append(f"Аккаунт: {query.account or 'не указан'}")
    parts.append(
        f"Заявленная сумма: {query.claimed_amount if query.claimed_amount is not None else 'не указана'}"
    )
    parts.append(f"Найдено транзакций: {len(transaction_reports)}")
    parts.append(f"Ошибок PaymentsThread всего: {result.get('payment_errors_total', 0)}")
    parts.append(f"Циклов Validator всего: {result.get('validator_cycles_total', 0)}")
    parts.append("")

    log_sources = result.get("log_sources", {})
    if log_sources:
        parts.append("Источники логов:")
        parts.append(f"- DPSKiosk: {log_sources.get('kiosk_log') or 'не найден'}")
        parts.append(f"- PaymentsThread: {log_sources.get('payments_log') or 'не найден'}")
        parts.append(f"- Validator: {log_sources.get('validator_log') or 'не найден'}")
        parts.append("")

    if not transaction_reports:
        parts.append("По указанным данным транзакции не найдены.")
        return "\n".join(parts)

    for idx, item in enumerate(transaction_reports, start=1):
        tx = item["transaction"]
        payment_errors = item.get("payment_errors", [])
        validator_cycles = item.get("validator_cycles", [])
        validator_total = sum(getattr(cycle, "total_stacked", 0.0) for cycle in validator_cycles)

        validator_errors = []
        for cycle in validator_cycles:
            validator_errors.extend(getattr(cycle, "errors", []))

        has_errors = bool(tx.errors or payment_errors or validator_errors)

        parts.append(f"--- Транзакция {idx} ---")
        parts.append(tx.report())

        parts.append("")
        parts.append("Итог по всем логам:")
        if tx.completed and not has_errors:
            parts.append("Операция завершена успешно.")
        elif tx.completed:
            parts.append("Операция завершена в DPS, но в связанных логах обнаружены ошибки/предупреждения.")
        else:
            parts.append("Операция не завершена в DPS.")

        parts.append("")
        parts.append("Ошибки PaymentsThread:")
        parts.append(format_payment_errors(payment_errors))

        parts.append("")
        parts.append("Циклы Validator:")
        parts.append(format_validator_cycles(validator_cycles))
        parts.append("")
        parts.append("Сравнение сумм DPS / Validator:")
        parts.append(f"- По таблице DPS: {tx.total_inserted} TJS")
        parts.append(f"- По Validator: {validator_total:g} TJS")

        if validator_total > 0 and tx.total_inserted > 0:
            diff_validator = Decimal(str(tx.total_inserted)) - Decimal(str(validator_total))
            parts.append(f"- Разница DPS - Validator: {diff_validator} TJS")
        elif validator_total > 0 and tx.total_inserted == 0:
            parts.append("- В DPS нет таблицы купюр, но Validator зафиксировал принятые купюры.")
        elif validator_total == 0:
            parts.append("- Validator не зафиксировал уложенные купюры для этой транзакции.")

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