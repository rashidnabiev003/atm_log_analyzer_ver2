from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable

from configs import patterns
from parser.reader import read_log_records
from parser.time_utils import parse_log_timestamp


@dataclass
class ValidatorStateEvent:
    state: int
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
    raw_errors: list[str] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        required = {20, 21, 128, 23, 129}
        found = {event.state for event in self.states}
        return required.issubset(found)

def extract_validator_cycles_from_records(records: Iterable[str]) -> list[ValidatorBillCycle]:
    cycles: list[ValidatorBillCycle] = []
    current_cycle: ValidatorBillCycle | None = None

    for line_no, record in enumerate(records, start=1):
        timestamp = parse_log_timestamp(record)

        if patterns.VALIDATOR_ENABLE_BILL_RE.search(record):
            if current_cycle is not None:
                cycles.append(current_cycle)

            current_cycle = ValidatorBillCycle(
                started_at=timestamp,
                line_start=line_no,
            )

        if current_cycle is not None:
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

        if patterns.VALIDATOR_DISABLE_BILL_RE.search(record):
            if current_cycle is not None:
                current_cycle.finished_at = timestamp
                current_cycle.line_end = line_no
                cycles.append(current_cycle)
                current_cycle = None

    if current_cycle is not None:
        cycles.append(current_cycle)

    return cycles


def extract_validator_cycles(path: str | Path) -> list[ValidatorBillCycle]:
    return extract_validator_cycles_from_records(read_log_records(path))