from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from django.conf import settings
import oracledb


_oracle_client_initialized = False


def init_client() -> None:
    global _oracle_client_initialized
    if _oracle_client_initialized:
        return

    try:
        oracledb.init_oracle_client(lib_dir=settings.ORACLE_CLIENT_LIB_DIR)
    except Exception as exc:
        if "already initialized" not in str(exc).lower():
            raise
    _oracle_client_initialized = True


@contextmanager
def oracle_connection() -> Iterator[oracledb.Connection]:
    init_client()
    dsn = f"{settings.ORACLE_HOST}:{settings.ORACLE_PORT}/{settings.ORACLE_SERVICE_NAME}"
    conn = oracledb.connect(
        user=settings.ORACLE_USER,
        password=settings.ORACLE_PASSWORD,
        dsn=dsn,
    )
    try:
        yield conn
    finally:
        conn.close()


def fetch_all_dicts(cursor: oracledb.Cursor) -> list[dict]:
    columns = [column[0].lower() for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]
