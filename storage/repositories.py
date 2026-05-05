from decimal import Decimal
from typing import Any

from storage.db_models import OperationInfo, PaymentInfo
from storage.mysql_client import MysqlClient
from storage import sql_queries


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


class OperationRepository:
    """
    DB #1:
    name, id_терминала, pay_date, account, summa
    """

    def __init__(self, client: MysqlClient) -> None:
        self.client = client

    def get_operation(
        self,
        *,
        account: str | None,
        phone_number: str | None,
    ) -> OperationInfo | None:
        search_value = account or phone_number

        if not search_value:
            return None

        row = self.client.fetch_one(
            sql_queries.OPERATION_SQL,
            (search_value,),
        )

        if row is None:
            return None

        return OperationInfo(
            name=_str_or_none(row.get("name")),
            terminal_id=_str_or_none(row.get("id_терминала") or row.get("terminal_id")),
            pay_date=row.get("pay_date"),
            account=_str_or_none(row.get("account")),
            summa=_decimal_or_none(row.get("summa")),
        )


class PaymentRepository:
    """
    DB #2:
    платежи аккаунта, session_id, поиск платежа по session_id.
    """

    def __init__(self, client: MysqlClient) -> None:
        self.client = client

    def get_payment_by_account(self, *, account: str) -> PaymentInfo | None:
        row = self.client.fetch_one(
            sql_queries.PAYMENT_BY_ACCOUNT_SQL,
            (account,),
        )

        if row is None:
            return None

        return PaymentInfo(
            session_id=_str_or_none(row.get("session_id")),
            account=_str_or_none(row.get("account") or account),
            payment_id=_str_or_none(row.get("payment_id")),
            status=_str_or_none(row.get("status")),
            summa=_decimal_or_none(row.get("summa")),
        )

    def get_payment_by_session(self, *, session_id: str) -> PaymentInfo | None:
        row = self.client.fetch_one(
            sql_queries.PAYMENT_BY_SESSION_SQL,
            (session_id,),
        )

        if row is None:
            return None

        return PaymentInfo(
            session_id=session_id,
            account=_str_or_none(row.get("account")),
            payment_id=_str_or_none(row.get("payment_id")),
            status=_str_or_none(row.get("status")),
            summa=_decimal_or_none(row.get("summa")),
        )