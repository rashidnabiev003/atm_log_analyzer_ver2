from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Bill:
    """Represents an inserted bill (denomination and quantity)."""

    denomination: int
    count: int

    @property
    def total(self) -> int:
        """Return the total value of this bill bundle."""
        return self.denomination * self.count

@dataclass
class DetectedError:
    code: str
    title: str
    category: str
    severity: str
    line_no: int
    raw: str
    conclusion: str

@dataclass
class Transaction:
    """Encapsulates all information related to one user transaction."""

    session_id: Optional[str]
    phone: Optional[str]
    account: Optional[str]
    bills: List[Bill] = field(default_factory=list)
    errors: list[DetectedError] = field(default_factory=list)
    cash_collection_completed: bool = False
    completed: bool = False
    bill_row_keys: set[str] = field(default_factory=set)
    expected_amount: Optional[float] = None      
    credited_amount: Optional[float] = None      
    comission_amount: Optional[float] = None    
    local_datetime: Optional[str] = None
    named_fields: dict[str, str] = field(default_factory=dict)

    started_at: datetime | None = None
    completed_at: datetime | None = None

    bill_table_seen: bool = False
    dps_note_bill_keys: set[str] = field(default_factory=set)
    dps_stacked_bill_values: list[float] = field(default_factory=list)


    @property
    def total_inserted(self) -> int:
        """Sum of all bill values inserted during the transaction."""
        return sum(bill.total for bill in self.bills)

    def status(self) -> str:
        if not self.has_financial_activity():
            return "NO_OPERATION"

        if self.completed and not self.errors:
            return "SUCCESS"

        if self.errors:
            return "FAILED"

        return "INCOMPLETE"
    
    def has_financial_activity(self) -> bool:
        return (
            bool(self.bills)
            or bool(self.named_fields)
            or self.expected_amount is not None
            or self.credited_amount is not None
            or self.comission_amount is not None
            or self.cash_collection_completed
        )

    def conclusion(self) -> str:
        reasons: list[str] = []

        if not self.has_financial_activity():
            return "Сессия открыта/закрыта без финансовой операции"

        seen_error_conclusions = set()
        
        for err in self.errors:
            key = (err.code, err.conclusion)
            if key in seen_error_conclusions:
                continue

            seen_error_conclusions.add(key)
            reasons.append(f"{err.title}: {err.conclusion}")

        if not self.completed:
            if self.cash_collection_completed:
                reasons.append(
                    "Платёжный этап завершён через Initializing payment complete"
                )
            else:
                reasons.append("Транзакция не завершена")

        if self.expected_amount is not None and self.credited_amount is not None:
            if self.comission_amount is not None:
                expected_credited = float(self.expected_amount) - float(self.comission_amount)

                if round(expected_credited, 2) != round(float(self.credited_amount), 2):
                    reasons.append(
                        f"Некорректное зачисление по NamedFields: "
                        f"AMOUNTALL={self.expected_amount}, "
                        f"COMISSION={self.comission_amount}, "
                        f"ожидаемый AMOUNT={expected_credited}, "
                        f"фактический AMOUNT={self.credited_amount}"
                    )
            else:
                reasons.append(
                    "AMOUNTALL и AMOUNT найдены, но COMISSION не найдена — "
                    "полную проверку AMOUNTALL - COMISSION = AMOUNT выполнить нельзя"
                )

        if self.total_inserted > 0 and self.expected_amount is not None:
            if round(float(self.total_inserted), 2) != round(float(self.expected_amount), 2):
                reasons.append(
                    f"Сумма по таблице купюр {self.total_inserted} "
                    f"не совпадает с AMOUNTALL {self.expected_amount}"
                )

        if not reasons:
            reasons.append("Операция завершена успешно")

        return "; ".join(reasons)

    def report(self) -> str:
        """Format a detailed report string for this transaction."""
        bill_list = [(b.denomination, b.count) for b in self.bills]

        if self.errors:
            grouped = {}

            for err in self.errors:
                key = (
                    err.code,
                    err.title,
                    err.category,
                    err.severity,
                    err.conclusion,
                )

                if key not in grouped:
                    grouped[key] = {"error": err, "count": 0}

                grouped[key]["count"] += 1

            errors_text = "\n".join(
                (
                    f"- [{item['error'].severity}] {item['error'].code}: {item['error'].title}"
                    f"{' x' + str(item['count']) if item['count'] > 1 else ''}\n"
                    f"  Категория: {item['error'].category}\n"
                    f"  Строка: {item['error'].line_no}\n"
                    f"  Вывод: {item['error'].conclusion}\n"
                    f"  Пример фрагмента: {item['error'].raw[:500]}"
                )
                for item in grouped.values()
            )
        else:
            errors_text = "нет"

        named_fields_text = (
        "\n".join(f"- {k}={v}" for k, v in sorted(self.named_fields.items()))
        if self.named_fields
        else "нет"
        )

        return (
            f"Сессия: {self.session_id}\n"
            f"Телефон: {self.phone}\n"
            f"Аккаунт: {self.account}\n"
            f"Внесено по таблице купюр: {self.total_inserted} TJS (купюры: {bill_list})\n"
            f"AMOUNTALL: {self.expected_amount if self.expected_amount is not None else 'N/A'}\n"
            f"COMISSION: {self.comission_amount if self.comission_amount is not None else 'N/A'}\n"
            f"AMOUNT: {self.credited_amount if self.credited_amount is not None else 'N/A'}\n"
            f"LOCAL_DATIME: {self.local_datetime if self.local_datetime is not None else 'N/A'}\n"
            f"Статус: {self.status()}\n"
            f"Ошибки:\n{errors_text}\n"
            f"NamedFields:\n{named_fields_text}\n"
        )
