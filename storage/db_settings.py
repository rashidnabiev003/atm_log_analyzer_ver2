import os
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()

@dataclass(frozen=True)
class MsDbSettings:
    driver: str
    server: str
    port: str | None
    database: str
    user: str
    password: str | None
    option: str | None


@dataclass(frozen=True)
class MainDbSettings:
    server: str
    database: str
    username: str
    password: str
    port: int 



def load_msdb_settings() -> MsDbSettings:
    return MsDbSettings(
        driver=os.getenv("MSDB_DRIVER"),
        server=os.getenv("MSDB_SERVER"),
        port=os.getenv("MSDB_PORT"),
        database=os.getenv("MSDB_DATABASE"),
        user=os.getenv("MSDB_USER"),
        password=os.getenv("MSDB_PASSWORD"),
        option=os.getenv("MSDB_OPTION"),
    )


def load_main_db_settings() -> MainDbSettings:
    return MainDbSettings(
        server=os.getenv("DB_SERVER"),
        database=os.getenv("DB_DATABASE"),
        username=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        port=int(os.getenv("DB_PORT")),
    )