from decimal import Decimal

from db.db_utils import ClientInfoDbHandle, LogPathsDbHandle
from db.models import InvestigationContext


class InvestigationContextProvider:
    """
    Собирает всё, что нужно pipeline:

    - данные клиента из DB #1;
    - пути к логам из DB #2;
    - claimed_amount из CLI, если оператор его указал.
    """

    def __init__(
        self,
        *,
        client_db: ClientInfoDbHandle,
        logs_db: LogPathsDbHandle,
    ) -> None:
        self.client_db = client_db
        self.logs_db = logs_db

    def build(
        self,
        *,
        phone_number: str | None,
        account: str | None,
        claimed_amount: Decimal | None,
    ) -> InvestigationContext:
        client_info = self.client_db.get_client_info(
            phone_number=phone_number,
            account=account,
        )

        final_phone = phone_number or (
            client_info.phone_number if client_info is not None else None
        )

        final_account = account or (
            client_info.account if client_info is not None else None
        )

        if not final_phone and not final_account:
            raise ValueError("Не удалось определить ни телефон, ни аккаунт клиента.")

        log_paths = self.logs_db.get_log_paths(
            phone_number=final_phone,
            account=final_account,
            client_info=client_info,
        )

        return InvestigationContext(
            phone_number=final_phone,
            account=final_account,
            claimed_amount=claimed_amount,
            log_paths=log_paths,
            client_info=client_info,
        )