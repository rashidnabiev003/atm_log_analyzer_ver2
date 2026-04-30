from dataclasses import dataclass
import re
from typing import Pattern


@dataclass(frozen=True)
class ErrorRule:
    code: str
    title: str
    category: str
    severity: str
    pattern: Pattern[str]
    conclusion: str