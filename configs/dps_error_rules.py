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
        code="STACKER_LENGTH_ERROR",
        title="Ошибка прохождения купюры / возможное замятие",
        category="cash_acceptor",
        severity="critical",
        pattern=re.compile(
            r"(?:stacker|staker)_opened\s*=\s*false\s*[:.=]?\s*(?:Lenght|Length)_error"
            r"|(?:Lenght|Length)_error",
            re.IGNORECASE,
        ),
        conclusion=(
            "Обнаружена ошибка Lenght/Length_error. Вероятно, купюра застряла "
            "или некорректно прошла внутри купюроприёмника."
        ),
    ),
    ErrorRule(
        code="PAYMENT_PACKET_LOADING_ERROR",
        title="Ошибка загрузки платежного пакета",
        category="payment_processing",
        severity="high",
        pattern=re.compile(
            r"Payment\s*packet\s*loading\s*error|Paymentpacketloadingerror",
            re.IGNORECASE,
        ),
        conclusion=(
            "Терминал не смог загрузить или сформировать платежный пакет. "
            "Деньги могли быть приняты устройством, но платеж мог не уйти дальше в процессинг."
        ),
    ),
    ErrorRule(
        code="STACKER_VALIDATION_ERROR",
        title="Ошибка валидации купюры",
        category="cash_acceptor",
        severity="high",
        pattern=re.compile(
            r"stacker_opened\s*=\s*false\s*\.?\s*Validation_error|Validation_error",
            re.IGNORECASE,
        ),
        conclusion=(
            "Купюра не прошла валидацию. Возможна ситуация, когда терминал "
            "увидел купюру, но не принял её как корректную."
        ),
    ),
    ErrorRule(
        code="STACKER_TRANSITION_ERROR",
        title="Ошибка перехода состояния купюроприёмника",
        category="cash_acceptor",
        severity="high",
        pattern=re.compile(
            r"stacker_opened\s*=\s*false\s*\.?\s*(transition_error|trasition_error)"
            r"|transition_error|trasition_error",
            re.IGNORECASE,
        ),
        conclusion=(
            "Ошибка перехода состояния механизма купюроприёмника. Возможен сбой "
            "при перемещении купюры внутри устройства."
        ),
    ),
    ErrorRule(
        code="POWER_OFF_STATE_15",
        title="Выключение питания",
        category="terminal_power",
        severity="critical",
        pattern=re.compile(
            r"State\s*\[\s*15\s*\]\s*Выключение\s+питания",
            re.IGNORECASE,
        ),
        conclusion=(
            "В момент работы терминала обнаружено состояние выключения питания. "
            "Операция могла оборваться из-за отключения или перезапуска терминала."
        ),
    ),
    ErrorRule(
        code="BILL_EJECT_28",
        title="Выброс купюры",
        category="cash_acceptor",
        severity="medium",
        pattern=re.compile(
            r"#\s*28\s*:?\s*Выброс\s+купюры|#\s*28",
            re.IGNORECASE,
        ),
        conclusion=(
            "Зафиксирован выброс купюры. Купюра могла быть возвращена клиенту "
            "или перейти в проблемное состояние."
        ),
    ),
    ErrorRule(
    code="TERMINAL_STARTUP_DETECTED",
    title="Обнаружен запуск/перезапуск терминала",
    category="terminal_power",
    severity="medium",
    pattern=re.compile(
        r"\bVersion\s*=\s*\d+(?:\.\d+){2,4}"
        r"|Defines\s*=\s*.*\bKIOS_APP\b",
        re.IGNORECASE,
    ),
    conclusion=(
        "В DPS обнаружен блок запуска/перезапуска терминала. "
        "Если это произошло между действиями клиента, операция могла быть прервана."
        ),
    ),
    ErrorRule(
        code="STACKER_LENGTH_ERROR",
        title="Ошибка прохождения купюры / возможное замятие",
        category="cash_acceptor",
        severity="critical",
        pattern=re.compile(
            r"(?:stacker|staker)_opened\s*=\s*false\s*[:.]?\s*Length_error"
            r"|Length_error",
            re.IGNORECASE,
        ),
        conclusion=(
            "Обнаружена ошибка Lenght_error. Вероятно, купюра застряла "
            "или некорректно прошла внутри купюроприёмника."
        ),
    ),
    ErrorRule(
        code="STACKER_IDENTIFICATION_ERROR",
        title="Ошибка идентификации купюры",
        category="cash_acceptor",
        severity="high",
        pattern=re.compile(
            r"(?:stacker|staker)_opened\s*=\s*false\s*[:.]?\s*Identification_error"
            r"|Identification_error",
            re.IGNORECASE,
        ),
        conclusion=(
            "Купюроприёмник не смог идентифицировать купюру. "
            "Возможна проблема распознавания или прохождения купюры."
        ),
    ),
    ErrorRule(
        code="STACKER_VERIFICATION_ERROR",
        title="Ошибка проверки купюры",
        category="cash_acceptor",
        severity="high",
        pattern=re.compile(
            r"(?:stacker|staker)_opened\s*=\s*false\s*[:.]?\s*Verification_error"
            r"|Verification_error",
            re.IGNORECASE,
        ),
        conclusion=(
            "Купюра не прошла проверку. Возможна проблема валидации или сбой купюроприёмника."
        ),
    ),
    ErrorRule(
        code="STACKER_INSERTION_ERROR",
        title="Ошибка вставки / подачи купюры",
        category="cash_acceptor",
        severity="high",
        pattern=re.compile(
            r"(?:stacker|staker)_opened\s*=\s*false\s*[:.]?\s*Insertion_error"
            r"|Insertion_error",
            re.IGNORECASE,
        ),
        conclusion=(
            "Обнаружена ошибка подачи купюры. Купюра могла быть некорректно принята механизмом."
        ),
    ),
]