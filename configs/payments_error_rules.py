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
        code="INSERTION_ERROR",
        title="Ошибка прохождения купюры / возможное замятие",
        category="cash_acceptor",
        severity="high",
        pattern=re.compile(
            r"Main\s*Failure\s*Description\s*\.?\s*Insertion_error|Insertion_error",
            re.IGNORECASE,
        ),
        conclusion=(
            "Обнаружена ошибка Lenght_error. Вероятно, купюра застряла "
            "или некорректно прошла внутри купюроприёмника."
        ),
    )
]