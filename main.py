from decimal import Decimal
import sys
import argparse
from typing import Iterable 

from configs.query import ClientQuery
from parser.reader import read_file
from parser.extractor import extract_transactions
from report.investigator import investigate
from report.reporter import print_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--phone", required=True)
    parser.add_argument("--account")
    parser.add_argument("--claimed-amount", type=Decimal)

    args = parser.parse_args()

    query = ClientQuery(
        phone_number=args.phone,
        account=args.account,
        claimed_amount=args.claimed_amount,
    )

    transactions = extract_transactions(read_file(args.path))
    result = investigate(transactions, query)

    print_report(result["transactions"])


if __name__ == "__main__":
    main()