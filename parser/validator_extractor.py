from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable

from configs import patterns
from configs.validator_error_rules import ERROR_RULES, ValidatorLogError
from parser.reader import read_log_records
from parser.time_utils import parse_log_timestamp


@dataclass
class ValidatorStateEvent:
    state: int
    line_no: int
    raw: str
    timestamp: datetime | None = None


@dataclass
class ValidatorStackedBill:
    nominal: float
    line_no: int
    raw: str
    timestamp: datetime | None = None


@dataclass
class ValidatorBillCycle:
    started_at: datetime | None
    finished_at: datetime | None = None
    line_start: int | None = None
    line_end: int | None = None
    states: list[ValidatorStateEvent] = field(default_factory=list)
    stacked_bills: list[ValidatorStackedBill] = field(default_factory=list)
    max_cash_values: list[float] = field(default_factory=list)
    errors: list[ValidatorLogError] = field(default_factory=list)
    closed_by: str | None = None

    @property
    def has_disable_bill(self) -> bool:
        return self.closed_by == "DISABLE_BILL"

    @property
    def is_complete(self) -> bool:
        required = {20, 21, 128, 23, 129}
        found = {event.state for event in self.states}
        return self.has_disable_bill and required.issubset(found)

    @property
    def total_stacked(self) -> float:
        return sum(bill.nominal for bill in self.stacked_bills)

    @property
    def initial_max_cash(self) -> float | None:
        if not self.max_cash_values:
            return None

        return self.max_cash_values[0]


    @property
    def remaining_max_cash(self) -> float | None:
        if not self.max_cash_values:
            return None

        return self.max_cash_values[-1]


    @property
    def total_by_max_cash_delta(self) -> float | None:
        if len(self.max_cash_values) < 2:
            return None

        delta = 0.0

        previous = self.max_cash_values[0]

        for current in self.max_cash_values[1:]:
            if current < previous:
                delta += previous - current

            previous = current

        return delta


def detect_validator_errors(record: str, line_no: int) -> list[ValidatorLogError]:
    timestamp = parse_log_timestamp(record)
    result: list[ValidatorLogError] = []

    for rule in ERROR_RULES:
        if rule.pattern.search(record):
            result.append(
                ValidatorLogError(
                    code=rule.code,
                    title=rule.title,
                    category=rule.category,
                    severity=rule.severity,
                    line_no=line_no,
                    raw=record,
                    conclusion=rule.conclusion,
                    timestamp=timestamp,
                )
            )

    return result


def parse_float(value: str) -> float | None:
    try:
        return float(value.replace(",", "."))
    except ValueError:
        return None


def extract_validator_cycles_from_records(records: Iterable[str]) -> list[ValidatorBillCycle]:
    cycles: list[ValidatorBillCycle] = []
    current_cycle: ValidatorBillCycle | None = None

    def close_current_cycle(
        *,
        finished_at: datetime | None,
        line_end: int,
        closed_by: str,
    ) -> None:
        nonlocal current_cycle

        if current_cycle is None:
            return

        current_cycle.finished_at = finished_at
        current_cycle.line_end = line_end
        current_cycle.closed_by = closed_by
        cycles.append(current_cycle)
        current_cycle = None

    for line_no, record in enumerate(records, start=1):
        timestamp = parse_log_timestamp(record)
        record_errors = detect_validator_errors(record, line_no)

        device_start = patterns.VALIDATOR_DEVICE_START_RE.search(record) is not None
        enable_bill = patterns.VALIDATOR_ENABLE_BILL_RE.search(record) is not None
        disable_bill = patterns.VALIDATOR_DISABLE_BILL_RE.search(record) is not None

        # Если устройство стартануло, а DISABLE BILL не было —
        # закрываем текущий цикл как незавершённый.
        if device_start and current_cycle is not None:
            close_current_cycle(
                finished_at=timestamp,
                line_end=line_no,
                closed_by="DEVICE_START",
            )

        # Если начался новый ENABLE BILL, а старый цикл не закрыт —
        # старый цикл закрываем как незавершённый.
        if enable_bill:
            if current_cycle is not None:
                close_current_cycle(
                    finished_at=timestamp,
                    line_end=line_no,
                    closed_by="NEXT_ENABLE_BILL",
                )

            current_cycle = ValidatorBillCycle(
                started_at=timestamp,
                line_start=line_no,
            )

        # Если ошибка встретилась вне ENABLE/DISABLE, не теряем её.
        if record_errors and current_cycle is None:
            current_cycle = ValidatorBillCycle(
                started_at=timestamp,
                line_start=line_no,
            )

        if current_cycle is not None:
            if record_errors:
                current_cycle.errors.extend(record_errors)

            state_match = patterns.VALIDATOR_STATE_RE.search(record)
            if state_match:
                current_cycle.states.append(
                    ValidatorStateEvent(
                        state=int(state_match.group("state")),
                        line_no=line_no,
                        raw=record,
                        timestamp=timestamp,
                    )
                )

            for max_cash_match in patterns.VALIDATOR_SET_MAX_CASH_RE.finditer(record):
                value = parse_float(max_cash_match.group("value"))
                if value is not None:
                    current_cycle.max_cash_values.append(value)

            for stacked_match in patterns.VALIDATOR_STACKED_NOMINAL_RE.finditer(record):
                value = parse_float(stacked_match.group("value"))
                if value is not None:
                    current_cycle.stacked_bills.append(
                        ValidatorStackedBill(
                            nominal=value,
                            line_no=line_no,
                            raw=record,
                            timestamp=timestamp,
                        )
                    )

        if disable_bill and current_cycle is not None:
            close_current_cycle(
                finished_at=timestamp,
                line_end=line_no,
                closed_by="DISABLE_BILL",
            )

    if current_cycle is not None:
        close_current_cycle(
            finished_at=current_cycle.finished_at,
            line_end=current_cycle.line_end or 0,
            closed_by="EOF",
        )

    return cycles


def extract_validator_cycles(path: str | Path) -> list[ValidatorBillCycle]:
    return extract_validator_cycles_from_records(read_log_records(path))