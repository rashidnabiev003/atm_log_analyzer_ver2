from collections.abc import Sequence
from typing import Any

import pymysql
from pymysql.cursors import DictCursor

from storage.db_settings import MysqlSettings, MsdbSettings


class MysqlClient:
    def __init__(self, settings: MysqlSettings | MsdbSettings) -> None:
        self.settings = settings

    def connect(self):
        username = getattr(self.settings, "username", None) or getattr(self.settings, "user", None)

        return pymysql.connect(
            host=self.settings.server,
            port=self.settings.port,
            user=username,
            password=self.settings.password,
            database=self.settings.database,
            charset="utf8mb4",
            cursorclass=DictCursor,
        )

    def fetch_one(self, query: str, params: Sequence[Any] | dict[str, Any] | None = None) -> dict[str, Any] | None:
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchone()

    def fetch_all(self, query: str, params: Sequence[Any] | dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return list(cursor.fetchall())