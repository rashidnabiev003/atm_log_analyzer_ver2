import argparse
from decimal import Decimal
from pathlib import Path

from configs.query import ClientQuery
from parser.reader import read_log_records
from parser.dps_extractor import extract_transactions
from parser.validator_extractor import extract_validator_cycles
from parser.payments_extractor import extract_payment_errors
from report.investigator import investigate
from report.reporter import print_investigation_report

from storage.context_provider import InvestigationContextProvider
from storage.mysql_client import MysqlClient
from storage.repositories import OperationRepository, PaymentRepository
from storage.db_settings import load_main_mysql_settings, load_msdb_settings


KIOSK_LOG_PATH = Path("log.txt")
PAYMENTS_THREAD_LOG_PATH = Path("PaymentsThread.log")
VALIDATOR_LOG_PATH = Path("Validator.log")


def required_existing_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")
    return str(path)


def optional_existing_file(path: Path) -> str | None:
    return str(path) if path.exists() else None


def build_context_provider() -> InvestigationContextProvider:
    operation_client = MysqlClient(load_msdb_settings())
    payment_client = MysqlClient(load_main_mysql_settings())

    return InvestigationContextProvider(
        operation_repo=OperationRepository(operation_client),
        payment_repo=PaymentRepository(payment_client),
        kiosk_log_path=KIOSK_LOG_PATH,
        payments_log_path=PAYMENTS_THREAD_LOG_PATH,
        validator_log_path=VALIDATOR_LOG_PATH,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument("phone", nargs="?", help="Номер телефона клиента")
    parser.add_argument("--phone", dest="phone_option", help="Номер телефона клиента")
    parser.add_argument("--account")
    parser.add_argument("--claimed-amount", type=Decimal)

    args = parser.parse_args()
    args.phone_number = args.phone_option or args.phone

    if not args.phone_number:
        parser.error("нужно указать номер телефона: main.py <phone> или main.py --phone <phone>")

    return args


def main() -> None:
    args = parse_args()
    context = build_context_provider().build(
    phone_number=args.phone_number,
    account=args.account,
    claimed_amount=args.claimed_amount,
    )

    query = ClientQuery(
        phone_number=context.phone_number,
        account=context.account,
        claimed_amount=context.claimed_amount,
    )

    transactions = extract_transactions(
        read_log_records(context.log_paths.kiosk_log)
    )

    validator_cycles = []
    if context.log_paths.validator_log:
        validator_cycles = extract_validator_cycles(context.log_paths.validator_log)

    payment_errors = []
    if context.log_paths.payments_log:
        payment_errors = extract_payment_errors(context.log_paths.payments_log)

    result = investigate(
        transactions,
        query,
        payment_errors=payment_errors,
        validator_cycles=validator_cycles,
    )

    result["log_sources"] = {
        "kiosk_log": context.log_paths.kiosk_log,
        "payments_log": context.log_paths.payments_log,
        "validator_log": context.log_paths.validator_log,
    }
    result["operation_info"] = context.operation
    result["payment_info"] = context.payment

    print_investigation_report(result)

if __name__ == "__main__":
    main()