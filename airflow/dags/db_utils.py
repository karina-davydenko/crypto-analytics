import os

import psycopg


def build_conninfo() -> str:
    host     = os.getenv('POSTGRES_HOST', 'postgres')
    port     = os.getenv('POSTGRES_PORT', '5432')
    dbname   = os.getenv('POSTGRES_DB', 'crypto_analytics')
    user     = os.getenv('POSTGRES_USER', 'airflow')
    password = os.getenv('POSTGRES_PASSWORD', 'airflow')
    return f"host={host} port={port} dbname={dbname} user={user} password={password}"


def get_connection() -> psycopg.Connection:
    return psycopg.connect(build_conninfo())
