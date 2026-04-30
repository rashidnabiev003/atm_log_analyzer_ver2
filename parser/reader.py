import io
import re
from typing import Iterator, TextIO
from pathlib import Path


LOG_RECORD_START_RE = re.compile(
    r"^\s*\d{2}[./]\d{2}[./]\d{4}\s+\d{2}[.:]\d{2}[.:]\d{2}[.:]\d{3}\b"
)

LOG_RECORD_SPLIT_RE = re.compile(
    r"(?=\d{2}[./]\d{2}[./]\d{4}\s+\d{2}[.:]\d{2}[.:]\d{2}[.:]\d{3}\b)"
)


def read_lines(file: TextIO, *, strip_newline: bool = True) -> Iterator[str]:
    for line in file:
        yield line.rstrip("\n") if strip_newline else line


def read_file(path: str | Path, *, encoding: str = "utf-8") -> Iterator[str]:
    with io.open(path, "r", encoding=encoding, errors="ignore") as f:
        for line in f:
            yield line.rstrip("\n")


def split_physical_line(line: str) -> list[str]:
    parts = [part.strip() for part in LOG_RECORD_SPLIT_RE.split(line) if part.strip()]
    return parts or [line]


def read_log_records(path: str | Path, *, encoding: str = "utf-8") -> Iterator[str]:
    current_record: list[str] = []

    with io.open(path, "r", encoding=encoding, errors="ignore") as f:
        for raw_line in f:
            physical_line = raw_line.rstrip("\n\r")

            for line in split_physical_line(physical_line):
                is_new_record = LOG_RECORD_START_RE.search(line) is not None

                if is_new_record and current_record:
                    yield "\n".join(current_record)
                    current_record = [line]
                else:
                    current_record.append(line)

    if current_record:
        yield "\n".join(current_record)