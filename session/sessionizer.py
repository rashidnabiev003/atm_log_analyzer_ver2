from typing import Iterable, List, Iterator

MAIN_PAGE_MARKER = 'Entered `main.html` page.' 


def split_sessions(lines: Iterable[str]) -> Iterator[List[str]]:
    """
    Функция генератор, которая разделяет сессии пользования терминалом
    """
    current_session: List[str] = []
    for line in lines:
        if MAIN_PAGE_MARKER in line:
            if current_session:
                yield current_session
                current_session = []
        current_session.append(line)
    if current_session:
        yield current_session
