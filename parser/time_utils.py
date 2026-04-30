from datetime import datetime
from configs import patterns


def parse_log_timestamp(text: str) -> datetime | None:
    match = patterns.LOG_TIMESTAMP_RE.search(text)
    if not match:
        return None

    raw = match.group("ts")

    formats = (
        "%d.%m.%Y %H.%M.%S.%f",
        "%d/%m/%Y %H.%M.%S.%f",
        "%d.%m.%Y %H:%M:%S.%f",
        "%d/%m/%Y %H:%M:%S.%f",
    )

    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            pass

    return None