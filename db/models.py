from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class LogPaths:
    kiosk_log: str
    payments_log: str | None = None
    validator_log: str | None = None


@dataclass(frozen=True)
class ClientInfo:
    phone_number: str | None = None
    account: str | None = None
    client_name: str | None = None
    operation_type: str | None = None
    transaction_id: str | None = None
    session_id: str | None = None
    extra: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class InvestigationContext:
    phone_number: str | None
    account: str | None
    claimed_amount: Decimal | None
    log_paths: LogPaths
    client_info: ClientInfo | None = None