from pathlib import Path
from typing import Protocol

from db.models import ClientInfo, LogPaths


class ClientInfoDbHandle(Protocol):
    """
    Ручка к DB #1.
    """

    def get_client_info(
        self,
        *,
        phone_number: str | None,
        account: str | None,
    ) -> ClientInfo | None:
        ...


class LogPathsDbHandle(Protocol):
    """
    Ручка к DB #2.
    """

    def get_log_paths(
        self,
        *,
        phone_number: str | None,
        account: str | None,
        client_info: ClientInfo | None,
    ) -> LogPaths:
        ...


class ManualClientInfoDbHandle:
    """
    Временная ручка вместо DB #1.
    """

    def get_client_info(
        self,
        *,
        phone_number: str | None,
        account: str | None,
    ) -> ClientInfo | None:
        return ClientInfo(
            phone_number=phone_number,
            account=account,
        )


class ManualLogPathsDbHandle:
    """
    Временная ручка вместо DB #2.
    """

    def __init__(
        self,
        *,
        kiosk_log: Path,
        payments_log: Path | None = None,
        validator_log: Path | None = None,
    ) -> None:
        self.kiosk_log = kiosk_log
        self.payments_log = payments_log
        self.validator_log = validator_log

    def get_log_paths(
        self,
        *,
        phone_number: str | None,
        account: str | None,
        client_info: ClientInfo | None,
    ) -> LogPaths:
        if not self.kiosk_log.exists():
            raise FileNotFoundError(f"Файл не найден: {self.kiosk_log}")

        payments_path = (
            str(self.payments_log)
            if self.payments_log is not None and self.payments_log.exists()
            else None
        )

        validator_path = (
            str(self.validator_log)
            if self.validator_log is not None and self.validator_log.exists()
            else None
        )

        return LogPaths(
            kiosk_log=str(self.kiosk_log),
            payments_log=payments_path,
            validator_log=validator_path,
        )


class PrimaryDbClientInfoHandle:
    """
    Заготовка под реальную DB #1.
    """

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def get_client_info(
        self,
        *,
        phone_number: str | None,
        account: str | None,
    ) -> ClientInfo | None:
        raise NotImplementedError(
            ""
        )


class SecondaryDbLogPathsHandle:
    """
    Заготовка под реальную DB #2.
    """

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def get_log_paths(
        self,
        *,
        phone_number: str | None,
        account: str | None,
        client_info: ClientInfo | None,
    ) -> LogPaths:
        raise NotImplementedError(
            ""
        )