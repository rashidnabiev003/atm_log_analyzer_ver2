import re
from dataclasses import dataclass
from typing import Pattern
from datetime import datetime


@dataclass(frozen=True)
class ErrorRule:
    code: str
    title: str
    category: str
    severity: str
    pattern: Pattern[str]
    conclusion: str

@dataclass
class ValidatorLogError:
    code: str
    title: str
    category: str
    severity: str
    line_no: int
    raw: str
    conclusion: str
    timestamp: datetime | None = None

ERROR_RULES = [
    ErrorRule(
        code="VALIDATOR_CASSETTE_REMOVED",
        title="Кассета снята",
        category="validator",
        severity="high",
        pattern=re.compile(r"State\s*\[\s*66\s*\]", re.IGNORECASE),
        conclusion="В Validator обнаружено состояние State [66]: кассета снята.",
    ),
    ErrorRule(
        code="VALIDATOR_BILL_REMOVED",
        title="Купюра снята",
        category="validator",
        severity="high",
        pattern=re.compile(r"State\s*\[\s*67\s*\]", re.IGNORECASE),
        conclusion="В Validator обнаружено состояние State [67]: купюра снята.",
    ),
    ErrorRule(
    code="VALIDATOR_HACKING",
    title="Взлом / нештатное вмешательство",
    category="validator_security",
    severity="critical",
    pattern=re.compile(r"State\s*\[\s*69\s*\]", re.IGNORECASE),
    conclusion="В Validator обнаружено состояние State [69]: возможное нештатное вмешательство.",
    ),
    ErrorRule(
        code="VALIDATOR_POWER_OFF",
        title="Выключение питания Validator",
        category="validator_power",
        severity="critical",
        pattern=re.compile(r"State\s*\[\s*16\s*\]", re.IGNORECASE),
        conclusion="В Validator обнаружено состояние State [16]: выключение питания.",
    ),
    ErrorRule(
        code="VALIDATOR_STACKER_LENGTH_ERROR",
        title="Ошибка прохождения купюры / возможное замятие",
        category="validator_cash_acceptor",
        severity="critical",
        pattern=re.compile(
            r"(?:stacker|staker)_opened\s*=\s*false\s*[:.]?\s*Lenght_error"
            r"|Lenght_error",
            re.IGNORECASE,
        ),
        conclusion="В Validator обнаружена ошибка Lenght_error. Возможна проблема прохождения купюры.",
    ),
    ErrorRule(
        code="VALIDATOR_STACKER_IDENTIFICATION_ERROR",
        title="Ошибка идентификации купюры",
        category="validator_cash_acceptor",
        severity="high",
        pattern=re.compile(
            r"(?:stacker|staker)_opened\s*=\s*false\s*[:.]?\s*Identification_error"
            r"|Identification_error",
            re.IGNORECASE,
        ),
        conclusion="В Validator обнаружена ошибка Identification_error.",
    ),
    ErrorRule(
        code="VALIDATOR_STACKER_VERIFICATION_ERROR",
        title="Ошибка проверки купюры",
        category="validator_cash_acceptor",
        severity="high",
        pattern=re.compile(
            r"(?:stacker|staker)_opened\s*=\s*false\s*[:.]?\s*Verification_error"
            r"|Verification_error",
            re.IGNORECASE,
        ),
        conclusion="В Validator обнаружена ошибка Verification_error.",
    ),
    ErrorRule(
        code="VALIDATOR_STACKER_INSERTION_ERROR",
        title="Ошибка подачи купюры",
        category="validator_cash_acceptor",
        severity="high",
        pattern=re.compile(
            r"(?:stacker|staker)_opened\s*=\s*false\s*[:.]?\s*Insertion_error"
            r"|Insertion_error",
            re.IGNORECASE,
        ),
        conclusion="В Validator обнаружена ошибка Insertion_error.",
    ),
    ErrorRule(
        code="VALIDATOR_MAIN_FAILURE_IDENTIFICATION",
        title="Validator: ошибка идентификации купюры",
        category="validator_cash_acceptor",
        severity="high",
        pattern=re.compile(
            r"Main\s+Failure\s+Description\s*:\s*Identification_error",
            re.IGNORECASE,
        ),
        conclusion="Validator сообщил Main Failure Description: Identification_error.",
    ),
    ErrorRule(
        code="VALIDATOR_MAIN_FAILURE_LENGTH",
        title="Validator: ошибка прохождения купюры / возможное замятие",
        category="validator_cash_acceptor",
        severity="critical",
        pattern=re.compile(
            r"Main\s+Failure\s+Description\s*:\s*(?:Lenght|Length)_error",
            re.IGNORECASE,
        ),
        conclusion="Validator сообщил Main Failure Description: Lenght/Length_error. Возможна проблема прохождения купюры.",
    ),
]