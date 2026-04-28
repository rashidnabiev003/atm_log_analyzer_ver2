from typing import Iterator, TextIO
import io


def read_lines(file: TextIO, *, strip_newline: bool = True) -> Iterator[str]:
    for line in file:
        yield line.rstrip("\n") if strip_newline else line


def read_file(path: str, *, encoding: str = "utf-8") -> Iterator[str]:
    with io.open(path, "r", encoding=encoding, errors="ignore") as f:
        for line in f:
            yield line.rstrip("\n")
