from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class OperationInfo:
    name: str | None
    terminal_id: str | None
    pay_date: datetime | None
    account: str | None
    summa: Decimal | None


@dataclass(frozen=True)
class PaymentInfo:
    session_id: str | None
    account: str | None
    payment_id: str | None = None
    status: str | None = None
    summa: Decimal | None = None


@dataclass(frozen=True)
class LogPaths:
    kiosk_log: str
    payments_log: str | None = None
    validator_log: str | None = None


@dataclass(frozen=True)
class InvestigationContext:
    phone_number: str | None
    account: str | None
    claimed_amount: Decimal | None
    operation: OperationInfo | None
    payment: PaymentInfo | None
    log_paths: LogPaths