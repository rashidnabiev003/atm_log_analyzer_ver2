from decimal import Decimal
from configs.query import ClientQuery
from configs.models import Transaction
from collections import Counter

def summarize_validator_cycles(cycles: list) -> dict:
    total_stacked = sum(float(getattr(cycle, "total_stacked", 0.0)) for cycle in cycles)

    max_cash_values: list[float] = []
    validator_errors = []
    incomplete_cycles = 0

    for cycle in cycles:
        max_cash_values.extend(getattr(cycle, "max_cash_values", []))
        validator_errors.extend(getattr(cycle, "errors", []))

        if not getattr(cycle, "is_complete", False):
            incomplete_cycles += 1

    initial_max_cash = max(max_cash_values) if max_cash_values else None
    remaining_max_cash = min(max_cash_values) if max_cash_values else None

    if initial_max_cash is not None and remaining_max_cash is not None:
        max_cash_delta = initial_max_cash - remaining_max_cash
    else:
        max_cash_delta = None

    return {
        "cycles_count": len(cycles),
        "incomplete_cycles": incomplete_cycles,
        "total_stacked": total_stacked,
        "initial_max_cash": initial_max_cash,
        "remaining_max_cash": remaining_max_cash,
        "max_cash_delta": max_cash_delta,
        "errors": validator_errors,
    }

def classify_operation(tx, payment_errors: list, validator_cycles: list) -> str:
    validator_errors = []
    validator_incomplete = False

    for cycle in validator_cycles:
        validator_errors.extend(getattr(cycle, "errors", []))
        if not getattr(cycle, "is_complete", False):
            validator_incomplete = True

    has_critical_or_high = any(
        getattr(err, "severity", "") in {"critical", "high"}
        for err in [*tx.errors, *payment_errors, *validator_errors]
    )

    has_any_warning = bool(tx.errors or payment_errors or validator_errors)

    if hasattr(tx, "has_financial_activity") and not tx.has_financial_activity():
        return "NO_OPERATION"

    if not tx.completed or validator_incomplete:
        return "INCOMPLETE"

    if has_critical_or_high:
        return "FAILED"

    if has_any_warning:
        return "SUSPICIOUS"

    return "SUCCESS"


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

    summary = summarize_validator_cycles(cycles)

    parts = [
        f"Циклов Validator: {summary['cycles_count']}",
        f"Незавершённых циклов: {summary['incomplete_cycles']}",
        f"Принято по Stacked nominal: {summary['total_stacked']:g} TJS",
        f"MaxCash начальный: {summary['initial_max_cash'] if summary['initial_max_cash'] is not None else 'N/A'}",
        f"MaxCash остаток: {summary['remaining_max_cash'] if summary['remaining_max_cash'] is not None else 'N/A'}",
        f"По разнице MaxCash: {summary['max_cash_delta'] if summary['max_cash_delta'] is not None else 'N/A'} TJS",
    ]

    if summary["max_cash_delta"] is not None and summary["total_stacked"] > 0:
        if round(summary["max_cash_delta"], 2) != round(summary["total_stacked"], 2):
            parts.append(
                f"Предупреждение: Stacked nominal={summary['total_stacked']:g} TJS, "
                f"а MaxCash delta={summary['max_cash_delta']:g} TJS"
            )

    if summary["errors"]:
        parts.append("Ошибки Validator:")
        parts.append(format_unique_errors(summary["errors"]))

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
        validator_summary = summarize_validator_cycles(validator_cycles)
        validator_total = validator_summary["total_stacked"]
        validator_max_cash_delta = validator_summary["max_cash_delta"]

        validator_errors = []
        for cycle in validator_cycles:
            validator_errors.extend(getattr(cycle, "errors", []))

        has_errors = bool(tx.errors or payment_errors or validator_errors)

        parts.append(f"--- Транзакция {idx} ---")
        parts.append(tx.report())

        parts.append("")
        operation_status = classify_operation(tx, payment_errors, validator_cycles)
        parts.append("")
        parts.append(f"Итоговая оценка: {operation_status}")

        if operation_status == "SUCCESS":
            parts.append("Операция успешна.")
        elif operation_status == "FAILED":
            parts.append("Операция неуспешна: обнаружены критичные ошибки.")
        elif operation_status == "SUSPICIOUS":
            parts.append("Операция подозрительна: есть предупреждения или расхождения.")
        elif operation_status == "INCOMPLETE":
            parts.append("Операция не завершена полностью.")
        elif operation_status == "NO_OPERATION":
            parts.append("Финансовая операция не выполнялась.")

        parts.append("")
        parts.append("Ошибки PaymentsThread:")
        parts.append(format_payment_errors(payment_errors))

        parts.append("")
        parts.append("Циклы Validator:")
        parts.append(format_validator_cycles(validator_cycles))
        parts.append("")
        parts.append("Сравнение сумм DPS / Validator:")
        parts.append(f"- По DPS: {tx.total_inserted} TJS")
        parts.append(f"- По Validator Stacked nominal: {validator_total:g} TJS")
        parts.append(
            f"- По Validator MaxCash delta: "
            f"{validator_max_cash_delta if validator_max_cash_delta is not None else 'N/A'} TJS"
        )

        if validator_total > 0 and tx.total_inserted > 0:
            diff_validator = Decimal(str(tx.total_inserted)) - Decimal(str(validator_total))
            parts.append(f"- Разница DPS - Validator Stacked: {diff_validator} TJS")

        if validator_max_cash_delta is not None and tx.total_inserted > 0:
            diff_max_cash = Decimal(str(tx.total_inserted)) - Decimal(str(validator_max_cash_delta))
            parts.append(f"- Разница DPS - Validator MaxCash: {diff_max_cash} TJS")

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