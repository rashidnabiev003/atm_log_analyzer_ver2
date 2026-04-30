from typing import Iterator, TextIO
from pathlib import Path
import io
import re


LOG_RECORD_START_RE = re.compile(
    r"^\s*\d{2}\.\d{2}\.\d{4}\s+\d{2}\.\d{2}\.\d{2}\.\d{3}\b"
)


def read_lines(file: TextIO, *, strip_newline: bool = True) -> Iterator[str]:
    for line in file:
        yield line.rstrip("\n") if strip_newline else line


def read_file(path: str | Path, *, encoding: str = "utf-8") -> Iterator[str]:
    with io.open(path, "r", encoding=encoding, errors="ignore") as f:
        for line in f:
            yield line.rstrip("\n")


def read_log_records(path: str | Path, *, encoding: str = "utf-8") -> Iterator[str]:
    current_record: list[str] = []

    with io.open(path, "r", encoding=encoding, errors="ignore") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")

            is_new_record = LOG_RECORD_START_RE.search(line) is not None

            if is_new_record and current_record:
                yield "\n".join(current_record)
                current_record = [line]
            else:
                current_record.append(line)

    if current_record:
        yield "\n".join(current_record)
