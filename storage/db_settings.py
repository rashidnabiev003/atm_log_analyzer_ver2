import os
from dataclasses import dataclass


@dataclass(frozen=True)
class MysqlSettings:
    server: str
    database: str
    username: str
    password: str
    port: int = 3306


@dataclass(frozen=True)
class MsdbSettings:
    driver: str | None
    server: str
    port: int
    database: str
    user: str
    password: str | None
    option: str | None


def load_main_mysql_settings() -> MysqlSettings:
    return MysqlSettings(
        server=os.getenv("DB_SERVER", ""),
        database=os.getenv("DB_DATABASE", ""),
        username=os.getenv("DB_USERNAME", ""),
        password=os.getenv("DB_PASSWORD", ""),
        port=int(os.getenv("DB_PORT", "3306")),
    )


def load_msdb_settings() -> MsdbSettings:
    return MsdbSettings(
        driver=os.getenv("MSDB_DRIVER"),
        server=os.getenv("MSDB_SERVER", ""),
        port=int(os.getenv("MSDB_PORT", "3306")),
        database=os.getenv("MSDB_DATABASE", ""),
        user=os.getenv("MSDB_USER", ""),
        password=os.getenv("MSDB_PASSWORD"),
        option=os.getenv("MSDB_OPTION"),
    )