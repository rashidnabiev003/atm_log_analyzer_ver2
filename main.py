import sys
from typing import Iterable

from parser.reader import read_file
from parser.extractor import extract_transactions
from report.reporter import print_report


def analyze_path(path: str) -> None:
    """Analyze a single log file and print a report."""
    lines: Iterable[str] = read_file(path)
    transactions = extract_transactions(lines)
    print_report(transactions)


def main(argv: Iterable[str]) -> None:
    """Parse command line arguments and run the analyzer."""
    args = list(argv)
    if not args or args[0] in {"-h", "--help"}:
        print("Usage: python -m atm_log_analyzer_modular.main <logfile>")
        return
    path = args[0]
    analyze_path(path)


if __name__ == "__main__":
    main(sys.argv[1:])