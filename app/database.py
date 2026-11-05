import os

import psycopg
from psycopg.rows import dict_row


def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if database_url is None:
        raise RuntimeError("Переменная окружения DATABASE_URL не задана")
    return psycopg.connect(database_url, row_factory=dict_row)