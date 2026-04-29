import sys
import argparse
from typing import Iterable 
from pathlib import Path

from configs.query import ClientQuery
from decimal import Decimal
from parser.reader import read_file
from parser.extractor import extract_transactions
from report.investigator import investigate
from report.reporter import print_investigation_report


def existing_file_or_none(path: str | None) -> str | None:
    if not path:
        return None

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")

    return str(p)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--kiosk-log",
        required=True,
        help="Путь к DPSKiosk.log",
    )

    parser.add_argument(
        "--payments-log",
        required=False,
        help="Путь к PaymentsThread.log",
    ) #TODO Анализ

    parser.add_argument(
        "--validator-log",
        required=False,
        help="Путь к Validator.log",
    )#TODO Анализ

    parser.add_argument("--phone", required=True)
    parser.add_argument("--account")
    parser.add_argument("--claimed-amount", type=Decimal)

    args = parser.parse_args()

    kiosk_log = existing_file_or_none(args.kiosk_log)
    payments_log = existing_file_or_none(args.payments_log)
    validator_log = existing_file_or_none(args.validator_log)

    query = ClientQuery(
        phone_number=args.phone,
        account=args.account,
        claimed_amount=args.claimed_amount,
    )

    transactions = extract_transactions(read_file(kiosk_log))

    result = investigate(transactions, query)

    result["log_sources"] = {
        "kiosk_log": kiosk_log,
        "payments_log": payments_log,
        "validator_log": validator_log,
    }

    print_investigation_report(result)


if __name__ == "__main__":
    main()