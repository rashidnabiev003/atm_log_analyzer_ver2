from dataclasses import dataclass, field
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
    completed: bool = False
    expected_amount: Optional[float] = None
    credited_amount: Optional[float] = None

    @property
    def total_inserted(self) -> int:
        """Sum of all bill values inserted during the transaction."""
        return sum(bill.total for bill in self.bills)

    def status(self) -> str:
        """Return a simple status string based on completion and errors."""
        if self.completed and not self.errors:
            return "SUCCESS"
        if self.errors:
            return "FAILED"
        return "INCOMPLETE"

    def conclusion(self) -> str:
        reasons: list[str] = []

        for err in self.errors:
            reasons.append(f"{err.title}: {err.conclusion}")

        if not self.completed:
            reasons.append("Транзакция не завершена")

        if self.expected_amount is not None and int(self.expected_amount) != self.total_inserted:
            reasons.append(
                f"Сумма купюр {self.total_inserted} не совпадает с суммой операции {self.expected_amount}"
            )

        if self.credited_amount is not None and int(self.credited_amount) != self.total_inserted:
            reasons.append(
                f"По купюрам внесено {self.total_inserted}, но зачислено {self.credited_amount}"
            )

        if not reasons:
            reasons.append("Операция завершена успешно")

        return "; ".join(reasons)

    def report(self) -> str:
        """Format a detailed report string for this transaction."""
        bill_list = [(b.denomination, b.count) for b in self.bills]
        return (
            f"Сессия: {self.session_id}\n"
            f"Телефон: {self.phone}\n"
            f"Аккаунт: {self.account}\n"
            f"Внесено: {self.total_inserted} TJS (купюры: {bill_list})\n"
            f"Ожидаемая сумма: {self.expected_amount if self.expected_amount is not None else 'N/A'}\n"
            f"Зачислено: {self.credited_amount if self.credited_amount is not None else 'N/A'}\n"
            f"Статус: {self.status()}\n"
            f"Ошибки: {', '.join(self.errors) if self.errors else 'нет'}\n"
            f"Вывод: {self.conclusion()}"
        )
