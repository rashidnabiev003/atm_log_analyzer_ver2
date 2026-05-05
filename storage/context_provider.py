from decimal import Decimal
from pathlib import Path

from storage.db_models import InvestigationContext, LogPaths
from storage.repositories import OperationRepository, PaymentRepository


class InvestigationContextProvider:
    def __init__(
        self,
        *,
        operation_repo: OperationRepository,
        payment_repo: PaymentRepository,
        kiosk_log_path: Path,
        payments_log_path: Path | None,
        validator_log_path: Path | None,
    ) -> None:
        self.operation_repo = operation_repo
        self.payment_repo = payment_repo
        self.kiosk_log_path = kiosk_log_path
        self.payments_log_path = payments_log_path
        self.validator_log_path = validator_log_path

    def build(
        self,
        *,
        phone_number: str | None,
        account: str | None,
        claimed_amount: Decimal | None,
        session_id: str | None = None,
    ) -> InvestigationContext:
        operation = self.operation_repo.get_operation(
            account=account,
            phone_number=phone_number,
        )

        final_account = account or (operation.account if operation else None)

        payment = None

        if session_id:
            payment = self.payment_repo.get_payment_by_session(session_id=session_id)
        elif final_account:
            payment = self.payment_repo.get_payment_by_account(account=final_account)

        if final_account is None and payment is not None:
            final_account = payment.account

        if not self.kiosk_log_path.exists():
            raise FileNotFoundError(f"Файл DPSKiosk не найден: {self.kiosk_log_path}")

        log_paths = LogPaths(
            kiosk_log=str(self.kiosk_log_path),
            payments_log=(
                str(self.payments_log_path)
                if self.payments_log_path and self.payments_log_path.exists()
                else None
            ),
            validator_log=(
                str(self.validator_log_path)
                if self.validator_log_path and self.validator_log_path.exists()
                else None
            ),
        )

        final_claimed_amount = claimed_amount
        if final_claimed_amount is None and operation is not None:
            final_claimed_amount = operation.summa

        return InvestigationContext(
            phone_number=phone_number,
            account=final_account,
            claimed_amount=final_claimed_amount,
            operation=operation,
            payment=payment,
            log_paths=log_paths,
        )