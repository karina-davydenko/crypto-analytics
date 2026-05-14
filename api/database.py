from collections.abc import Generator
from typing import cast

import psycopg
from psycopg.rows import DictRow, dict_row
from psycopg_pool import ConnectionPool

from settings import settings

# Глобальная переменная пула — None до вызова init_pool()
_pool: ConnectionPool[psycopg.Connection[DictRow]] | None = None


def init_pool() -> None:
    """Создаёт пул соединений. Вызывается один раз при старте FastAPI."""
    global _pool

    _pool = cast(
        ConnectionPool[psycopg.Connection[DictRow]],
        ConnectionPool(
            conninfo=settings.database_url,
            # dict_row: каждая строка из БД будет dict {"column": value}, а не tuple
            kwargs={"row_factory": dict_row},
            min_size=settings.db_pool_min_size,
            max_size=settings.db_pool_max_size,
            # open=True — открыть соединения сразу, не ждать первого запроса
            open=True,
        ),
    )


def close_pool() -> None:
    """Закрывает все соединения в пуле. Вызывается при остановке FastAPI."""
    if _pool is not None:
        _pool.close()


def get_cursor() -> Generator[psycopg.Cursor[DictRow], None, None]:
    """
    FastAPI dependency: берёт соединение из пула и выдаёт курсор эндпоинту.

    Dependency Injection — аналог useContext() в React:
    эндпоинт объявляет что ему нужен курсор (cur: Cursor),
    FastAPI сам вызывает get_cursor() и передаёт результат.

    yield вместо return нужен чтобы выполнить cleanup ПОСЛЕ ответа:
    FastAPI вызывает эндпоинт → получает ответ → возобновляет генератор →
    курсор закрывается → соединение возвращается в пул.
    """
    assert _pool is not None, "Пул не инициализирован — вызови init_pool() при старте"
    with _pool.connection() as conn:
        conn.execute("SET search_path TO gold, silver, public")
        with conn.cursor() as cur:
            yield cur
