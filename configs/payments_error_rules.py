from dataclasses import dataclass
import re
from typing import Pattern


@dataclass(frozen=True)
class ErrorRule:
    code: str
    title: str
    category: str
    severity: str
    pattern: Pattern[str]
    conclusion: str


ERROR_RULES = [
    ErrorRule(
        code="PAYMENT_FIRST_TAG_NOT_FOUND",
        title="First tag not found в платежном пакете",
        category="payment_packet",
        severity="high",
        pattern=re.compile(
            r"Error\s*:\s*First\s+tag\s+not\s+found",
            re.IGNORECASE,
        ),
        conclusion=(
            "В PaymentsThread найдено 'First tag not found'. "
            "Вероятно, платежный пакет был некорректно сформирован или не распознан обработчиком."
        ),
    ),
]