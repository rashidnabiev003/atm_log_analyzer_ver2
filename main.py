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


KIOSK_LOG_PATH = Path("log.txt")
PAYMENTS_THREAD_LOG_PATH = Path("PaymentsThread.log")
VALIDATOR_LOG_PATH = Path("Validator.log")


def required_existing_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")
    return str(path)


def optional_existing_file(path: Path) -> str | None:
    return str(path) if path.exists() else None


def get_log_sources() -> dict[str, str | None]:
    """
    Единая точка, где сейчас задаются пути к трём логам.

    Позже это место можно заменить на получение файлов/путей из БД.
    """
    return {
        "kiosk_log": required_existing_file(KIOSK_LOG_PATH),
        "payments_log": optional_existing_file(PAYMENTS_THREAD_LOG_PATH),
        "validator_log": optional_existing_file(VALIDATOR_LOG_PATH),
    }


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
    log_sources = get_log_sources()

    query = ClientQuery(
        phone_number=args.phone_number,
        account=args.account,
        claimed_amount=args.claimed_amount,
    )

    transactions = extract_transactions(read_log_records(log_sources["kiosk_log"]))

    validator_cycles = []
    if log_sources["validator_log"]:
        validator_cycles = extract_validator_cycles(log_sources["validator_log"])

    payment_errors = []
    if log_sources["payments_log"]:
        payment_errors = extract_payment_errors(log_sources["payments_log"])

    result = investigate(
        transactions,
        query,
        payment_errors=payment_errors,
        validator_cycles=validator_cycles,
    )
    result["log_sources"] = log_sources

    print_investigation_report(result)


if __name__ == "__main__":
    main()