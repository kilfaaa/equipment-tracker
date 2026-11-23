from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

import os

import psycopg
from psycopg import Connection
from psycopg.rows import DictRow, dict_row


def get_connection() -> Connection[DictRow]:
    database_url = os.getenv("DATABASE_URL")
    if database_url is None:
        raise RuntimeError("Переменная окружения DATABASE_URL не задана")
    return psycopg.connect(database_url, row_factory=dict_row)


@lru_cache
def get_engine() -> Engine:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("Переменная окружения DATABASE_URL не задана")
    return create_engine(database_url)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(get_engine())