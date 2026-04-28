import re
from typing import Iterable, List, Iterator


SESSION_ANCHOR_RE = re.compile(r"Entered\s+[`'\"“”‘’]?\s*main\.html\s*[`'\"“”‘’]?\s+page\.?",re.IGNORECASE)


def is_session_anchor(line: str) -> bool:
    return SESSION_ANCHOR_RE.search(line) is not None


def split_sessions(lines: Iterable[str]) -> Iterator[List[str]]:
    current_session: List[str] = []

    for line in lines:
        if is_session_anchor(line):
            if current_session:
                yield current_session
                current_session = []

        current_session.append(line)

    if current_session:
        yield current_session